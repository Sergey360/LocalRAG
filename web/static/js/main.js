(function () {
    const SETTINGS_STORAGE_KEY = 'localrag.settings.v1';
    const ROLE_KEYS = ['analyst', 'engineer', 'archivist'];
    const LEGACY_ROLE_IMAGE_ALIASES = {
        analyst: {
            cartographer: 'analyst',
            spymaster: 'strategist'
        },
        engineer: {
            artificer: 'engineer',
            runesmith: 'blacksmith',
            sapper: 'engineer'
        },
        archivist: {
            lorekeeper: 'archivist',
            chronicler: 'scribe',
            relickeeper: 'curator'
        }
    };
    const ANSWER_LANGUAGE_OPTIONS = ['interface', 'en', 'ru', 'nl', 'zh', 'he'];
    const ROLE_STYLE_OPTIONS = ['concise', 'balanced', 'detailed'];
    const MODEL_MANAGER_POLL_MS = 2000;
    const EMBEDDING_MODEL_MANAGER_POLL_MS = 2000;
    const MODEL_POLICY_ORDER = {
        default: ['qwen3.5:9b', 'qwen3:8b', 'qwen3:14b', 'gemma3:12b', 'aya-expanse:8b', 'qwen2.5:14b', 'qwen2.5:7b-instruct', 'phi3:mini'],
        en: ['qwen3.5:9b', 'qwen3:8b', 'qwen3:14b', 'gemma3:12b', 'phi3:mini', 'qwen2.5:14b', 'aya-expanse:8b', 'qwen2.5:7b-instruct'],
        ru: ['qwen3.5:9b', 'qwen3:8b', 'qwen3:14b', 'gemma3:12b', 'qwen2.5:14b', 'aya-expanse:8b', 'qwen2.5:7b-instruct', 'phi3:mini'],
        nl: ['qwen3.5:9b', 'qwen3:8b', 'gemma3:12b', 'qwen3:14b', 'aya-expanse:8b', 'qwen2.5:14b', 'phi3:mini'],
        zh: ['qwen3.5:9b', 'qwen3:8b', 'qwen3:14b', 'qwen2.5:14b', 'gemma3:12b', 'aya-expanse:8b', 'phi3:mini'],
        he: ['qwen3.5:9b', 'qwen3:8b', 'gemma3:12b', 'aya-expanse:8b', 'qwen3:14b', 'qwen2.5:14b', 'phi3:mini']
    };
    const SETTINGS_DEFAULTS = {
        historyLimit: 12,
        answerLanguage: 'interface',
        roleStyle: 'balanced',
        debugMode: false,
        rolePromptsByLang: {},
        roleImages: {},
        customRoles: [],
        preferredModel: ''
    };
    const CUSTOM_ROLE_ID_PREFIX = 'custom-';
    const CUSTOM_ROLE_ID_PATTERN = /^[a-z0-9][a-z0-9_-]{0,63}$/;
    let askRequestPending = false;
    let modelManagerPollHandle = null;
    let embeddingModelManagerPollHandle = null;
    let statusPollHandle = null;
    let lastModelManagerPayload = null;
    let lastEmbeddingModelManagerPayload = null;
    let lastDocsBrowserPayload = null;
    let activeSettingsTab = 'general';

    function getAppContainer(scope) {
        if (scope instanceof HTMLElement) {
            return scope.id === 'app' ? scope : (scope.closest('#app') || document.getElementById('app'));
        }
        return document.getElementById('app');
    }

    function escapeHtml(value) {
        return String(value || '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function readUiMessage(attrName, fallback) {
        const app = getAppContainer();
        if (app && app.dataset && app.dataset[attrName]) {
            return app.dataset[attrName];
        }
        const body = document.body;
        if (body && body.dataset && body.dataset[attrName]) {
            return body.dataset[attrName];
        }
        return fallback;
    }

    function readJsonScript(id, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const script = root.querySelector('#' + id) || document.getElementById(id);
        if (!script) {
            return {};
        }
        try {
            return JSON.parse(script.textContent || '{}');
        } catch (_) {
            return {};
        }
    }

    function getJsonScriptElement(id, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#' + id) || document.getElementById(id);
    }

    function normalizeServerProfile(raw, scope) {
        const src = raw && typeof raw === 'object' ? raw : {};
        return {
            customRoles: normalizeCustomRoles(src.customRoles || src.custom_roles, scope || document)
        };
    }

    function getServerProfile(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const script = getJsonScriptElement('server-profile-data', root);
        if (script) {
            const normalized = normalizeServerProfile(readJsonScript('server-profile-data', root), root);
            window.LocalRagServerProfile = normalized;
            return normalized;
        }
        if (!window.LocalRagServerProfile) {
            window.LocalRagServerProfile = normalizeServerProfile({}, root);
        }
        return normalizeServerProfile(window.LocalRagServerProfile, root);
    }

    function setServerProfile(profile, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const normalized = normalizeServerProfile(profile, root);
        window.LocalRagServerProfile = normalized;
        const script = getJsonScriptElement('server-profile-data', root);
        if (script) {
            script.textContent = JSON.stringify(normalized);
        }
        return normalized;
    }

    function getServerCustomRoles(scope) {
        return normalizeServerProfile(getServerProfile(scope), scope || document).customRoles;
    }

    function getLoadingMessage() {
        return readUiMessage('loadingMessage', 'Working on it...');
    }

    function getStaleMessage() {
        return readUiMessage('responseStaleMessage', 'Inputs changed. Submit the question again.');
    }

    function getDocsPathUpdatedMessage(pathValue) {
        return readUiMessage('docsPathUpdatedMessage', 'Documents path: {path}')
            .replace('{path}', String(pathValue || ''));
    }

    function getDocsPathUpdateFailedMessage() {
        return readUiMessage('docsPathUpdateFailedMessage', 'Failed to update documents path.');
    }

    function getDocsBrowserLoadingMessage() {
        return readUiMessage('docsBrowserLoadingMessage', 'Loading folders...');
    }

    function getDocsBrowserEmptyMessage() {
        return readUiMessage('docsBrowserEmptyMessage', 'No subfolders found.');
    }

    function getDocsBrowserErrorMessage() {
        return readUiMessage('docsBrowserErrorMessage', 'Failed to load folders.');
    }

    function getDocsInvalidPathMessage() {
        return readUiMessage('docsInvalidPathMessage', 'Failed to update documents path.');
    }

    function stopStatusPolling() {
        if (statusPollHandle) {
            window.clearTimeout(statusPollHandle);
            statusPollHandle = null;
        }
    }

    function startStatusPolling(delayMs) {
        stopStatusPolling();
        const timeout = Number.isFinite(Number(delayMs)) ? Number(delayMs) : 1400;
        statusPollHandle = window.setTimeout(function () {
            statusPollHandle = null;
            if (!window.htmx) {
                return;
            }
            const statusCard = document.getElementById('status-card');
            if (statusCard) {
                window.htmx.trigger(statusCard, 'refreshStatus');
            }
        }, timeout);
    }

    function syncStatusPolling() {
        const statusCard = document.getElementById('status-card');
        const statusCode = statusCard ? String(statusCard.dataset.statusCode || '').trim() : '';
        if (statusCode === 'indexing' || statusCode === 'loading') {
            startStatusPolling(1400);
            return;
        }
        stopStatusPolling();
    }

    window.startStatusPolling = startStatusPolling;

    function clampInt(value, min, max, fallback) {
        const parsed = Number.parseInt(String(value), 10);
        if (Number.isNaN(parsed)) {
            return fallback;
        }
        return Math.max(min, Math.min(max, parsed));
    }

    function normalizeRoleKey(value) {
        const role = String(value || '').trim().toLowerCase();
        return ROLE_KEYS.includes(role) ? role : 'analyst';
    }

    function normalizeRoleId(value) {
        const role = String(value || '').trim().toLowerCase();
        if (ROLE_KEYS.includes(role)) {
            return role;
        }
        return role.startsWith(CUSTOM_ROLE_ID_PREFIX) && CUSTOM_ROLE_ID_PATTERN.test(role) ? role : 'analyst';
    }

    function slugifyRoleSegment(value) {
        const text = String(value || '')
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
        return text || 'role';
    }

    function buildCustomRoleId(name, currentId) {
        const existing = normalizeRoleId(currentId);
        if (existing.startsWith(CUSTOM_ROLE_ID_PREFIX)) {
            return existing;
        }
        const slug = slugifyRoleSegment(name);
        return CUSTOM_ROLE_ID_PREFIX + slug;
    }

    function normalizeRoleStyle(value) {
        const style = String(value || '').trim().toLowerCase();
        return ROLE_STYLE_OPTIONS.includes(style) ? style : SETTINGS_DEFAULTS.roleStyle;
    }

    function normalizeCustomRoleDefaultStyle(value) {
        const style = String(value || '').trim().toLowerCase();
        return ROLE_STYLE_OPTIONS.includes(style) ? style : '';
    }

    function normalizeAnswerLanguageSetting(value) {
        const lang = String(value || '').trim().toLowerCase();
        return ANSWER_LANGUAGE_OPTIONS.includes(lang) ? lang : SETTINGS_DEFAULTS.answerLanguage;
    }

    function normalizePreferredModel(value) {
        return String(value || '').trim();
    }

    function getCurrentLang(scope) {
        const app = getAppContainer(scope);
        const raw = app && app.dataset ? app.dataset.lang : document.body.dataset.currentLang;
        return String(raw || 'en').trim().toLowerCase();
    }

    function getLanguageLabels(scope) {
        const parsed = readJsonScript('language-labels', scope);
        return parsed && typeof parsed === 'object' ? parsed : {};
    }

    function getModelManagerI18n(scope) {
        const parsed = readJsonScript('model-manager-i18n', scope);
        return parsed && typeof parsed === 'object' ? parsed : {};
    }

    function getModelText(key, scope, fallback) {
        const labels = getModelManagerI18n(scope);
        return labels[key] || fallback || key;
    }

    function getModelPolicyOrder(answerLanguage) {
        const normalized = String(answerLanguage || '').trim().toLowerCase();
        const primary = MODEL_POLICY_ORDER[normalized] || [];
        const fallback = MODEL_POLICY_ORDER.default || [];
        return Array.from(new Set(primary.concat(fallback)));
    }

    function getAnswerLanguageLabel(value, scope) {
        const labels = getLanguageLabels(scope);
        return labels[value] || value;
    }

    function getEffectiveAnswerLanguage(answerLanguageSetting, scope) {
        const normalized = normalizeAnswerLanguageSetting(answerLanguageSetting);
        return normalized === 'interface' ? getCurrentLang(scope) : normalized;
    }

    function getHistoryLimitUpperBound() {
        const slider = document.getElementById('settings-history-limit');
        if (!slider) {
            return 25;
        }
        return clampInt(slider.max, 1, 200, 25);
    }

    function getDefaultRolePromptGroups(scope) {
        const parsed = readJsonScript('role-prompt-defaults', scope);
        return parsed && typeof parsed === 'object' ? parsed : {};
    }

    function getDefaultRoleDefinitions(scope) {
        const parsed = readJsonScript('default-role-definitions', scope);
        return Array.isArray(parsed) ? parsed : [];
    }

    function getRoleImageCatalog(scope) {
        const parsed = readJsonScript('role-image-catalog', scope);
        return parsed && typeof parsed === 'object' ? parsed : {};
    }

    function getSharedRoleImageOptions(scope) {
        const catalog = getRoleImageCatalog(scope);
        const shared = catalog && catalog._shared && Array.isArray(catalog._shared.options)
            ? catalog._shared.options
            : [];
        if (shared.length) {
            return shared;
        }
        const analyst = catalog && catalog.analyst && Array.isArray(catalog.analyst.options)
            ? catalog.analyst.options
            : [];
        return analyst;
    }

    function getRoleImageOptionByValue(value, scope) {
        const options = getSharedRoleImageOptions(scope);
        const selected = String(value || '').trim();
        return options.find(function (option) {
            return option && option.value === selected;
        }) || options[0] || null;
    }

    function getSettingsI18n(scope) {
        const parsed = readJsonScript('settings-i18n', scope);
        return parsed && typeof parsed === 'object' ? parsed : {};
    }

    function getSettingsText(key, scope, fallback) {
        const labels = getSettingsI18n(scope);
        return labels[key] || fallback || key;
    }

    function getRoleImageSelect(role, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#settings-role-image-' + normalizeRoleKey(role))
            || document.getElementById('settings-role-image-' + normalizeRoleKey(role));
    }

    function getRoleImagePreview(role, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#settings-role-image-preview-' + normalizeRoleKey(role))
            || document.getElementById('settings-role-image-preview-' + normalizeRoleKey(role));
    }

    function getDocsPathInput(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#settings-docs-path') || document.getElementById('settings-docs-path');
    }

    function getEmbeddingModelSelect(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#settings-embedding-model-select') || document.getElementById('settings-embedding-model-select');
    }

    function getEmbeddingModelCustomInput(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#settings-embedding-model-custom') || document.getElementById('settings-embedding-model-custom');
    }

    function getEmbeddingModelsStatus(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#embedding-models-pull-status') || document.getElementById('embedding-models-pull-status');
    }

    function getInstalledEmbeddingModelsList(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#installed-embedding-models-list') || document.getElementById('installed-embedding-models-list');
    }

    function getRecommendedEmbeddingModelsList(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#recommended-embedding-models-list') || document.getElementById('recommended-embedding-models-list');
    }

    function getCurrentEmbeddingModel(scope) {
        const select = getEmbeddingModelSelect(scope);
        const customInput = getEmbeddingModelCustomInput(scope);
        const currentValue = select
            ? String(select.dataset.currentValue || select.getAttribute('data-current-value') || '').trim()
            : '';
        if (currentValue) {
            return currentValue;
        }
        return customInput ? String(customInput.value || '').trim() : '';
    }

    function setCurrentEmbeddingModel(scope, value) {
        const model = String(value || '').trim();
        const select = getEmbeddingModelSelect(scope);
        const customInput = getEmbeddingModelCustomInput(scope);
        if (select) {
            select.dataset.currentValue = model;
        }
        if (customInput) {
            customInput.dataset.currentValue = model;
        }
    }

    function syncEmbeddingModelInputVisibility(scope) {
        const select = getEmbeddingModelSelect(scope);
        const customInput = getEmbeddingModelCustomInput(scope);
        if (!select || !customInput) {
            return;
        }
        const isCustom = String(select.value || '').trim() === 'custom';
        customInput.hidden = !isCustom;
        customInput.disabled = !isCustom;
    }

    function setEmbeddingModelControls(modelName, scope) {
        const select = getEmbeddingModelSelect(scope);
        const customInput = getEmbeddingModelCustomInput(scope);
        const value = String(modelName || '').trim();
        if (!select) {
            return;
        }
        const hasDirectOption = Array.from(select.options || []).some(function (option) {
            return option && option.value === value;
        });
        if (hasDirectOption && value) {
            select.value = value;
            if (customInput) {
                customInput.value = '';
            }
        } else {
            select.value = 'custom';
            if (customInput) {
                customInput.value = value;
            }
        }
        syncEmbeddingModelInputVisibility(scope);
    }

    function resolveEmbeddingModelSetting(scope) {
        const select = getEmbeddingModelSelect(scope);
        const customInput = getEmbeddingModelCustomInput(scope);
        if (!select) {
            return '';
        }
        const selected = String(select.value || '').trim();
        if (selected === 'custom') {
            return customInput ? String(customInput.value || '').trim() : '';
        }
        return selected;
    }

    function selectEmbeddingModel(modelName, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const value = String(modelName || '').trim();
        if (!value) {
            return;
        }
        setCurrentEmbeddingModel(root, value);
        setEmbeddingModelControls(value, root);
        if (typeof showAlert === 'function') {
            showAlert(
                getSettingsText('settings_embedding_model_selected', root, 'Selected embedding model: {model}. Click Apply settings to reindex.')
                    .replace('{model}', value),
                'info',
                3500
            );
        }
    }

    function getDocsBrowserCard(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#docs-browser-card') || document.getElementById('docs-browser-card');
    }

    function getDocsBrowserOverlay(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#docs-browser-overlay') || document.getElementById('docs-browser-overlay');
    }

    function getDocsBrowserCurrent(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#docs-browser-current-path') || document.getElementById('docs-browser-current-path');
    }

    function getDocsBrowserList(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#docs-browser-list') || document.getElementById('docs-browser-list');
    }

    function getDocsBrowserUpButton(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#docs-browser-up-btn') || document.getElementById('docs-browser-up-btn');
    }

    function getDocsBrowserSearch(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#docs-browser-search') || document.getElementById('docs-browser-search');
    }

    function getDocsBrowserUseButton(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#docs-browser-use-btn') || document.getElementById('docs-browser-use-btn');
    }

    function getDocsBrowserCloseButton(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#docs-browser-close-btn') || document.getElementById('docs-browser-close-btn');
    }

    function getSettingsTabButtons(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return Array.from(root.querySelectorAll('[data-settings-tab]'));
    }

    function getSettingsPanes(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return Array.from(root.querySelectorAll('[data-settings-pane]'));
    }

    function activateSettingsTab(tabName, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const target = String(tabName || 'general').trim().toLowerCase() || 'general';
        let matched = false;

        getSettingsTabButtons(root).forEach(function (button) {
            const isActive = String(button.getAttribute('data-settings-tab') || '') === target;
            button.classList.toggle('is-active', isActive);
            button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
            if (isActive) {
                matched = true;
            }
        });

        getSettingsPanes(root).forEach(function (pane) {
            const isActive = String(pane.getAttribute('data-settings-pane') || '') === target;
            pane.classList.toggle('is-active', isActive);
            pane.hidden = !isActive;
        });

        activeSettingsTab = matched ? target : 'general';
        if (!matched && target !== 'general') {
            activateSettingsTab('general', root);
        }
    }

    function getRoleLabelHidden(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#role-label-hidden') || document.getElementById('role-label-hidden');
    }

    function getCustomRoleList(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#settings-custom-roles-list') || document.getElementById('settings-custom-roles-list');
    }

    function getCustomRoleEditId(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-edit-id') || document.getElementById('custom-role-edit-id');
    }

    function getCustomRoleNameInput(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-name') || document.getElementById('custom-role-name');
    }

    function getCustomRoleDescriptionInput(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-description') || document.getElementById('custom-role-description');
    }

    function getCustomRolePromptInput(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-prompt') || document.getElementById('custom-role-prompt');
    }

    function getCustomRoleImageSelect(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-image') || document.getElementById('custom-role-image');
    }

    function getCustomRoleImagePreview(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-image-preview') || document.getElementById('custom-role-image-preview');
    }

    function getCustomRoleAnswerLanguageSelect(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-answer-language') || document.getElementById('custom-role-answer-language');
    }

    function getCustomRoleDefaultModelSelect(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-default-model') || document.getElementById('custom-role-default-model');
    }

    function getCustomRoleDefaultStyleSelect(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-role-default-style') || document.getElementById('custom-role-default-style');
    }

    function getCustomRolesExportButton(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-roles-export-btn') || document.getElementById('custom-roles-export-btn');
    }

    function getCustomRolesImportButton(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-roles-import-btn') || document.getElementById('custom-roles-import-btn');
    }

    function getCustomRolesImportInput(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-roles-import-file') || document.getElementById('custom-roles-import-file');
    }

    function getCustomRolesResetButton(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        return root.querySelector('#custom-roles-reset-btn') || document.getElementById('custom-roles-reset-btn');
    }

    function getAvailableModelNames(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const modelEl = root.querySelector('#model') || document.getElementById('model');
        if (!modelEl || !modelEl.options) {
            return [];
        }
        const seen = new Set();
        return Array.from(modelEl.options || []).map(function (option) {
            return normalizePreferredModel(option && option.value);
        }).filter(function (value) {
            if (!value || seen.has(value)) {
                return false;
            }
            seen.add(value);
            return true;
        });
    }

    function getCurrentModelSelection(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const modelEl = root.querySelector('#model') || document.getElementById('model');
        if (!modelEl) {
            return '';
        }
        return normalizePreferredModel(modelEl.value);
    }

    function refreshCustomRoleDefaultModelSelect(scope, selectedValue) {
        const root = scope instanceof HTMLElement ? scope : document;
        const select = getCustomRoleDefaultModelSelect(root);
        if (!select) {
            return;
        }
        const selectedModel = normalizePreferredModel(selectedValue != null ? selectedValue : select.value);
        const models = getAvailableModelNames(root).slice();
        if (selectedModel && !models.includes(selectedModel)) {
            models.unshift(selectedModel);
        }

        select.innerHTML = '';

        const inheritOption = document.createElement('option');
        inheritOption.value = '';
        inheritOption.textContent = getSettingsText(
            'settings_custom_roles_default_model_inherit',
            root,
            'Browser default model'
        );
        select.appendChild(inheritOption);

        models.forEach(function (modelName) {
            const option = document.createElement('option');
            option.value = modelName;
            option.textContent = modelName;
            select.appendChild(option);
        });

        select.value = selectedModel && models.includes(selectedModel) ? selectedModel : '';
    }

    function normalizeRoleImageChoice(role, value, scope) {
        const key = normalizeRoleKey(role);
        const catalog = getRoleImageCatalog(scope);
        const roleCatalog = catalog[key] && typeof catalog[key] === 'object' ? catalog[key] : {};
        const options = Array.isArray(roleCatalog.options) ? roleCatalog.options : [];
        const allowed = options
            .map(function (option) {
                return String((option && option.value) || '').trim();
            })
            .filter(Boolean);
        const aliases = LEGACY_ROLE_IMAGE_ALIASES[key] && typeof LEGACY_ROLE_IMAGE_ALIASES[key] === 'object'
            ? LEGACY_ROLE_IMAGE_ALIASES[key]
            : {};
        let selected = String(value || '').trim();
        if (selected && !allowed.includes(selected) && aliases[selected]) {
            selected = aliases[selected];
        }
        if (selected && allowed.includes(selected)) {
            return selected;
        }
        if (typeof roleCatalog.default === 'string' && allowed.includes(roleCatalog.default)) {
            return roleCatalog.default;
        }
        return allowed[0] || '';
    }

    function normalizeRoleImageMap(rawMap, scope) {
        const source = rawMap && typeof rawMap === 'object' ? rawMap : {};
        const normalized = {};
        ROLE_KEYS.forEach(function (role) {
            normalized[role] = normalizeRoleImageChoice(role, source[role], scope);
        });
        return normalized;
    }

    function getDefaultRoleImages(scope) {
        return normalizeRoleImageMap({}, scope);
    }

    function normalizeSharedRoleImageChoice(value, scope) {
        const option = getRoleImageOptionByValue(value, scope);
        return option ? option.value : '';
    }

    function normalizeCustomRoles(rawRoles, scope) {
        const source = Array.isArray(rawRoles) ? rawRoles : [];
        const usedIds = new Set();
        const normalized = [];

        source.forEach(function (entry, index) {
            if (!entry || typeof entry !== 'object') {
                return;
            }
            const name = String(entry.name || entry.label || '').trim();
            const description = String(entry.description || '').trim();
            const prompt = String(entry.prompt || '').trim();
            let id = String(entry.id || '').trim().toLowerCase();
            if (!id || !CUSTOM_ROLE_ID_PATTERN.test(id) || ROLE_KEYS.includes(id)) {
                id = buildCustomRoleId(name || ('role-' + String(index + 1)), '');
            }
            while (usedIds.has(id) || ROLE_KEYS.includes(id)) {
                id = id + '-x';
            }
            usedIds.add(id);
            normalized.push({
                id: id,
                name: name || ('Custom role ' + String(index + 1)),
                description: description,
                prompt: prompt,
                image: normalizeSharedRoleImageChoice(entry.image, scope),
                answerLanguage: normalizeAnswerLanguageSetting(entry.answerLanguage),
                defaultModel: normalizePreferredModel(entry.defaultModel),
                defaultStyle: normalizeCustomRoleDefaultStyle(entry.defaultStyle || entry.default_style)
            });
        });

        return normalized;
    }

    function getDraftCustomRoles(scope) {
        const draft = Array.isArray(window.LocalRagDraftCustomRoles) ? window.LocalRagDraftCustomRoles : [];
        return normalizeCustomRoles(draft, scope || document);
    }

    function setDraftCustomRoles(roles, scope) {
        window.LocalRagDraftCustomRoles = normalizeCustomRoles(roles, scope || document);
    }

    function normalizeRolePromptMap(rawMap, defaultMap) {
        const source = rawMap && typeof rawMap === 'object' ? rawMap : {};
        const defaults = defaultMap && typeof defaultMap === 'object' ? defaultMap : {};
        const normalized = {};
        ROLE_KEYS.forEach(function (role) {
            const fallback = typeof defaults[role] === 'string' ? defaults[role] : '';
            const value = typeof source[role] === 'string' ? source[role].trim() : '';
            normalized[role] = value || fallback;
        });
        return normalized;
    }

    function getDefaultRolePrompts(scope, answerLanguage) {
        const groups = getDefaultRolePromptGroups(scope);
        const effectiveLanguage = getEffectiveAnswerLanguage(answerLanguage || SETTINGS_DEFAULTS.answerLanguage, scope);
        return normalizeRolePromptMap(groups[effectiveLanguage], {});
    }

    function getRolePromptInput(role, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const key = normalizeRoleKey(role);
        return root.querySelector('#settings-role-prompt-' + key) || document.getElementById('settings-role-prompt-' + key);
    }

    function getRolePromptsForScope(settings, scope) {
        const safe = normalizeSettings(settings);
        const effectiveAnswerLanguage = getEffectiveAnswerLanguage(safe.answerLanguage, scope);
        const defaultMap = getDefaultRolePrompts(scope, effectiveAnswerLanguage);
        const stored = safe.rolePromptsByLang && safe.rolePromptsByLang[effectiveAnswerLanguage]
            ? safe.rolePromptsByLang[effectiveAnswerLanguage]
            : {};
        return normalizeRolePromptMap(stored, defaultMap);
    }

    function getAllRoleDefinitions(settings, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const safe = normalizeSettings(settings);
        const defaultRoles = getDefaultRoleDefinitions(root).map(function (role) {
            const selectedImage = normalizeRoleImageChoice(role.id, safe.roleImages[role.id], root);
            const option = getRoleImageOptionByValue(selectedImage, root);
            return {
                id: role.id,
                name: role.label,
                description: role.description,
                prompt: '',
                image: selectedImage,
                imageSrc: option && option.src ? option.src : role.image_src,
                builtin: true
            };
        });
        const customRoles = normalizeCustomRoles(safe.customRoles, root).map(function (role) {
            const option = getRoleImageOptionByValue(role.image, root);
            return {
                id: role.id,
                name: role.name,
                description: role.description,
                prompt: role.prompt,
                image: role.image,
                imageSrc: option && option.src ? option.src : '',
                answerLanguage: normalizeAnswerLanguageSetting(role.answerLanguage),
                defaultModel: normalizePreferredModel(role.defaultModel),
                defaultStyle: normalizeCustomRoleDefaultStyle(role.defaultStyle),
                builtin: false
            };
        });
        return defaultRoles.concat(customRoles);
    }

    function getEffectiveAnswerLanguageForRole(roleDefinition, settings, scope) {
        const safeSettings = normalizeSettings(settings || getSettings());
        if (roleDefinition && !roleDefinition.builtin) {
            const roleAnswerLanguage = normalizeAnswerLanguageSetting(roleDefinition.answerLanguage);
            if (roleAnswerLanguage && roleAnswerLanguage !== 'interface') {
                return roleAnswerLanguage;
            }
        }
        return getEffectiveAnswerLanguage(safeSettings.answerLanguage, scope);
    }

    function getResolvedModelForRole(roleDefinition, settings, scope) {
        const safeSettings = normalizeSettings(settings || getSettings());
        const options = getAvailableModelNames(scope);
        const customRoleModel = roleDefinition && !roleDefinition.builtin
            ? normalizePreferredModel(roleDefinition.defaultModel)
            : '';

        if (customRoleModel && options.includes(customRoleModel)) {
            return customRoleModel;
        }

        const preferredModel = normalizePreferredModel(safeSettings.preferredModel);
        if (preferredModel && options.includes(preferredModel)) {
            return preferredModel;
        }

        const currentModel = getCurrentModelSelection(scope);
        if (currentModel && options.includes(currentModel)) {
            return currentModel;
        }

        const effectiveAnswerLanguage = getEffectiveAnswerLanguageForRole(roleDefinition, safeSettings, scope);
        return getModelPolicyOrder(effectiveAnswerLanguage).find(function (candidate) {
            return options.includes(candidate);
        }) || '';
    }

    function getEffectiveRoleStyleForRole(roleDefinition, settings) {
        const safeSettings = normalizeSettings(settings || getSettings());
        if (roleDefinition && !roleDefinition.builtin) {
            const roleStyle = normalizeCustomRoleDefaultStyle(roleDefinition.defaultStyle);
            if (roleStyle) {
                return roleStyle;
            }
        }
        return normalizeRoleStyle(safeSettings.roleStyle);
    }

    function getRoleDefinitionById(roleId, settings, scope) {
        const targetId = normalizeRoleId(roleId);
        return getAllRoleDefinitions(settings || getSettings(), scope).find(function (role) {
            return role.id === targetId;
        }) || null;
    }

    function syncCustomRolePrompt(scope, settings) {
        const root = scope instanceof HTMLElement ? scope : document;
        const hidden = root.querySelector('#custom-role-prompt-hidden') || document.getElementById('custom-role-prompt-hidden');
        const roleHidden = root.querySelector('#role-hidden') || document.getElementById('role-hidden');
        const roleLabelHidden = getRoleLabelHidden(root);
        if (!hidden || !roleHidden) {
            return;
        }
        const role = normalizeRoleId(roleHidden.value);
        const roleDefinition = getRoleDefinitionById(role, settings || getSettings(), root);
        const prompts = getRolePromptsForScope(settings || getSettings(), root);
        const answerLanguageHidden = root.querySelector('#answer-language-hidden') || document.getElementById('answer-language-hidden');
        const roleStyleHidden = root.querySelector('#role-style-hidden') || document.getElementById('role-style-hidden');
        const safeSettings = normalizeSettings(settings || getSettings());
        const effectiveAnswerLanguage = getEffectiveAnswerLanguageForRole(roleDefinition, safeSettings, root);
        const effectiveRoleStyle = getEffectiveRoleStyleForRole(roleDefinition, safeSettings);
        if (roleStyleHidden) {
            roleStyleHidden.value = effectiveRoleStyle;
        }
        if (roleDefinition && !roleDefinition.builtin) {
            hidden.value = roleDefinition.prompt || '';
            if (roleLabelHidden) {
                roleLabelHidden.value = roleDefinition.name || role;
            }
            if (answerLanguageHidden) {
                answerLanguageHidden.value = effectiveAnswerLanguage;
            }
            applyPreferredModel(safeSettings, root, roleDefinition);
            return;
        }
        hidden.value = prompts[normalizeRoleKey(role)] || '';
        if (roleLabelHidden && roleDefinition) {
            roleLabelHidden.value = roleDefinition.name || role;
        }
        if (answerLanguageHidden) {
            answerLanguageHidden.value = effectiveAnswerLanguage;
        }
        applyPreferredModel(safeSettings, root, roleDefinition);
    }

    function refreshSettingsDefaultsFromDom() {
        const historyHidden = document.getElementById('history-limit-hidden');
        const roleStyleHidden = document.getElementById('role-style-hidden');
        const maxLimit = getHistoryLimitUpperBound();

        if (historyHidden) {
            SETTINGS_DEFAULTS.historyLimit = clampInt(
                historyHidden.value,
                1,
                maxLimit,
                SETTINGS_DEFAULTS.historyLimit
            );
        }
        if (roleStyleHidden) {
            SETTINGS_DEFAULTS.roleStyle = normalizeRoleStyle(roleStyleHidden.value);
        }
    }

    function normalizeSettings(raw) {
        const src = raw && typeof raw === 'object' ? raw : {};
        const maxLimit = getHistoryLimitUpperBound();
        const rolePromptsByLang = {};

        if (src.rolePromptsByLang && typeof src.rolePromptsByLang === 'object') {
            Object.keys(src.rolePromptsByLang).forEach(function (lang) {
                const langKey = String(lang || '').trim().toLowerCase();
                if (!langKey) {
                    return;
                }
                rolePromptsByLang[langKey] = normalizeRolePromptMap(src.rolePromptsByLang[langKey], {});
            });
        }

        return {
            historyLimit: clampInt(src.historyLimit, 1, maxLimit, SETTINGS_DEFAULTS.historyLimit),
            answerLanguage: normalizeAnswerLanguageSetting(src.answerLanguage),
            roleStyle: normalizeRoleStyle(src.roleStyle),
            debugMode: !!src.debugMode,
            rolePromptsByLang: rolePromptsByLang,
            roleImages: normalizeRoleImageMap(src.roleImages, document),
            customRoles: normalizeCustomRoles(src.customRoles, document),
            preferredModel: normalizePreferredModel(src.preferredModel)
        };
    }

    function loadSettings() {
        const serverRoles = getServerCustomRoles(document);
        try {
            const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
            if (!raw) {
                const defaults = normalizeSettings(SETTINGS_DEFAULTS);
                defaults.customRoles = serverRoles;
                return defaults;
            }
            const parsed = JSON.parse(raw);
            const normalized = normalizeSettings(parsed);
            normalized.customRoles = serverRoles.length ? serverRoles : normalized.customRoles;
            return normalized;
        } catch (_) {
            const defaults = normalizeSettings(SETTINGS_DEFAULTS);
            defaults.customRoles = serverRoles;
            return defaults;
        }
    }

    function saveSettings(settings) {
        const safe = normalizeSettings(settings);
        const persisted = {
            historyLimit: safe.historyLimit,
            answerLanguage: safe.answerLanguage,
            roleStyle: safe.roleStyle,
            debugMode: safe.debugMode,
            rolePromptsByLang: safe.rolePromptsByLang,
            roleImages: safe.roleImages,
            preferredModel: safe.preferredModel
        };
        try {
            localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(persisted));
        } catch (_) {
            // Ignore storage failures (private mode / quota / disabled storage).
        }
    }

    function getSettings() {
        if (!window.LocalRagSettings) {
            window.LocalRagSettings = loadSettings();
        }
        return window.LocalRagSettings;
    }

    function getCurrentSettingsState(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const modal = root.querySelector('#settings-modal') || document.getElementById('settings-modal');
        if (modal && !modal.hidden) {
            return collectSettingsFromModal(root);
        }
        return getSettings();
    }

    function syncServerCustomRolesToSettings(customRoles, scope, baseSettings) {
        const root = scope instanceof HTMLElement ? scope : document;
        const settings = normalizeSettings(baseSettings || getCurrentSettingsState(root));
        settings.customRoles = normalizeCustomRoles(customRoles, root);
        window.LocalRagSettings = settings;
        saveSettings(settings);
        applySettingsToUi(settings, root);
        return settings;
    }

    function updateRolePromptScopeLabel(answerLanguageSetting, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const label = root.querySelector('#settings-role-prompts-scope') || document.getElementById('settings-role-prompts-scope');
        if (!label) {
            return;
        }
        const template = label.dataset.template || 'Editing prompts for: {language}';
        const effectiveAnswerLanguage = getEffectiveAnswerLanguage(answerLanguageSetting, root);
        label.textContent = template.replace('{language}', getAnswerLanguageLabel(effectiveAnswerLanguage, root));
    }

    function applyRoleImages(settings, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const safe = normalizeSettings(settings);
        const catalog = getRoleImageCatalog(root);

        ROLE_KEYS.forEach(function (role) {
            const choice = normalizeRoleImageChoice(role, safe.roleImages[role], root);
            const roleCatalog = catalog[role] && typeof catalog[role] === 'object' ? catalog[role] : {};
            const options = Array.isArray(roleCatalog.options) ? roleCatalog.options : [];
            const selectedOption = options.find(function (option) {
                return option && option.value === choice;
            }) || options[0];
            const img = root.querySelector('[data-role-image="' + role + '"]')
                || document.querySelector('[data-role-image="' + role + '"]');
            const select = getRoleImageSelect(role, root);
            const preview = getRoleImagePreview(role, root);

            if (select) {
                select.value = choice;
            }
            if (img && selectedOption && selectedOption.src) {
                img.src = selectedOption.src;
            }
            if (preview && selectedOption && selectedOption.src) {
                preview.src = selectedOption.src;
                preview.alt = selectedOption.label || role;
            }
        });
    }

    function syncRoleImagePreview(role, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const key = normalizeRoleKey(role);
        const catalog = getRoleImageCatalog(root);
        const roleCatalog = catalog[key] && typeof catalog[key] === 'object' ? catalog[key] : {};
        const options = Array.isArray(roleCatalog.options) ? roleCatalog.options : [];
        const select = getRoleImageSelect(key, root);
        const preview = getRoleImagePreview(key, root);
        if (!select || !preview || options.length === 0) {
            return;
        }
        const choice = normalizeRoleImageChoice(key, select.value, root);
        const selectedOption = options.find(function (option) {
            return option && option.value === choice;
        }) || options[0];
        if (!selectedOption || !selectedOption.src) {
            return;
        }
        preview.src = selectedOption.src;
        preview.alt = selectedOption.label || key;
    }

    function syncCustomRoleImagePreview(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const select = getCustomRoleImageSelect(root);
        const preview = getCustomRoleImagePreview(root);
        if (!select || !preview) {
            return;
        }
        const selectedOption = getRoleImageOptionByValue(select.value, root);
        if (!selectedOption || !selectedOption.src) {
            return;
        }
        preview.src = selectedOption.src;
        preview.alt = selectedOption.label || 'role';
    }

    function renderRoleSelector(settings, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const container = root.querySelector('#role-selector') || document.getElementById('role-selector');
        if (!container) {
            return;
        }
        const roles = getAllRoleDefinitions(settings || getSettings(), root);
        const hidden = root.querySelector('#role-hidden') || document.getElementById('role-hidden');
        const selectedRadio = root.querySelector('input[name="role-selector"]:checked')
            || document.querySelector('input[name="role-selector"]:checked');
        const requestedRole = normalizeRoleId(
            (hidden && hidden.value) || (selectedRadio && selectedRadio.value) || 'analyst'
        );
        const availableIds = roles.map(function (role) { return role.id; });
        const selectedRole = availableIds.includes(requestedRole) ? requestedRole : 'analyst';

        container.innerHTML = roles.map(function (role) {
            const roleId = escapeAttribute(role.id);
            const roleName = escapeHtml(role.name || role.id);
            const roleDescription = escapeHtml(role.description || '');
            const imageSrc = escapeAttribute(role.imageSrc || '');
            const checked = role.id === selectedRole ? ' checked' : '';
            const selectedClass = role.id === selectedRole ? ' is-selected' : '';
            return ''
                + '<label class="role-card' + selectedClass + '" for="role-' + roleId + '">'
                + '  <input type="radio" id="role-' + roleId + '" name="role-selector" value="' + roleId + '"' + checked + '>'
                + '  <img src="' + imageSrc + '" alt="' + roleName + '">'
                + '  <span class="role-copy">'
                + '    <span class="role-name-row"><span class="role-name">' + roleName + '</span></span>'
                + '    <span class="role-note">' + roleDescription + '</span>'
                + '  </span>'
                + '</label>';
        }).join('');

        if (hidden) {
            hidden.value = selectedRole;
        }
    }

    function getCurrentCustomRoleFormData(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const editId = getCustomRoleEditId(root);
        const nameInput = getCustomRoleNameInput(root);
        const descriptionInput = getCustomRoleDescriptionInput(root);
        const promptInput = getCustomRolePromptInput(root);
        const imageSelect = getCustomRoleImageSelect(root);
        const answerLanguageSelect = getCustomRoleAnswerLanguageSelect(root);
        const defaultModelSelect = getCustomRoleDefaultModelSelect(root);
        const defaultStyleSelect = getCustomRoleDefaultStyleSelect(root);
        return {
            id: editId ? String(editId.value || '').trim() : '',
            name: nameInput ? String(nameInput.value || '').trim() : '',
            description: descriptionInput ? String(descriptionInput.value || '').trim() : '',
            prompt: promptInput ? String(promptInput.value || '').trim() : '',
            image: normalizeSharedRoleImageChoice(imageSelect ? imageSelect.value : '', root),
            answerLanguage: normalizeAnswerLanguageSetting(answerLanguageSelect ? answerLanguageSelect.value : SETTINGS_DEFAULTS.answerLanguage),
            defaultModel: normalizePreferredModel(defaultModelSelect ? defaultModelSelect.value : ''),
            defaultStyle: normalizeCustomRoleDefaultStyle(defaultStyleSelect ? defaultStyleSelect.value : '')
        };
    }

    function clearCustomRoleEditor(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const editId = getCustomRoleEditId(root);
        const nameInput = getCustomRoleNameInput(root);
        const descriptionInput = getCustomRoleDescriptionInput(root);
        const promptInput = getCustomRolePromptInput(root);
        const imageSelect = getCustomRoleImageSelect(root);
        const answerLanguageSelect = getCustomRoleAnswerLanguageSelect(root);
        const defaultModelSelect = getCustomRoleDefaultModelSelect(root);
        const defaultStyleSelect = getCustomRoleDefaultStyleSelect(root);
        if (editId) {
            editId.value = '';
        }
        if (nameInput) {
            nameInput.value = '';
        }
        if (descriptionInput) {
            descriptionInput.value = '';
        }
        if (promptInput) {
            promptInput.value = '';
        }
        if (imageSelect) {
            imageSelect.value = normalizeSharedRoleImageChoice('', root);
        }
        if (answerLanguageSelect) {
            answerLanguageSelect.value = SETTINGS_DEFAULTS.answerLanguage;
        }
        refreshCustomRoleDefaultModelSelect(root, '');
        if (defaultModelSelect) {
            defaultModelSelect.value = '';
        }
        if (defaultStyleSelect) {
            defaultStyleSelect.value = '';
        }
        syncCustomRoleImagePreview(root);
        const saveBtn = root.querySelector('#custom-role-save-btn') || document.getElementById('custom-role-save-btn');
        if (saveBtn) {
            saveBtn.textContent = getSettingsText('settings_custom_roles_save', root, 'Save role');
        }
    }

    function populateCustomRoleEditor(role, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const editId = getCustomRoleEditId(root);
        const nameInput = getCustomRoleNameInput(root);
        const descriptionInput = getCustomRoleDescriptionInput(root);
        const promptInput = getCustomRolePromptInput(root);
        const imageSelect = getCustomRoleImageSelect(root);
        const answerLanguageSelect = getCustomRoleAnswerLanguageSelect(root);
        const defaultModelSelect = getCustomRoleDefaultModelSelect(root);
        const defaultStyleSelect = getCustomRoleDefaultStyleSelect(root);
        if (!role) {
            clearCustomRoleEditor(root);
            return;
        }
        if (editId) {
            editId.value = role.id || '';
        }
        if (nameInput) {
            nameInput.value = role.name || '';
        }
        if (descriptionInput) {
            descriptionInput.value = role.description || '';
        }
        if (promptInput) {
            promptInput.value = role.prompt || '';
        }
        if (imageSelect) {
            imageSelect.value = normalizeSharedRoleImageChoice(role.image, root);
        }
        if (answerLanguageSelect) {
            answerLanguageSelect.value = normalizeAnswerLanguageSetting(role.answerLanguage);
        }
        refreshCustomRoleDefaultModelSelect(root, role.defaultModel);
        if (defaultModelSelect) {
            defaultModelSelect.value = normalizePreferredModel(role.defaultModel);
        }
        if (defaultStyleSelect) {
            defaultStyleSelect.value = normalizeCustomRoleDefaultStyle(role.defaultStyle);
        }
        syncCustomRoleImagePreview(root);
        const saveBtn = root.querySelector('#custom-role-save-btn') || document.getElementById('custom-role-save-btn');
        if (saveBtn) {
            saveBtn.textContent = getSettingsText('settings_custom_roles_update', root, 'Update role');
        }
    }

    function renderCustomRoleList(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const container = getCustomRoleList(root);
        if (!container) {
            return;
        }
        const roles = getDraftCustomRoles(root);
        if (!roles.length) {
            container.innerHTML = '<p class="muted custom-roles-empty">'
                + escapeHtml(getSettingsText('settings_custom_roles_empty', root, 'No custom roles yet.'))
                + '</p>';
            return;
        }
        container.innerHTML = roles.map(function (role) {
            const option = getRoleImageOptionByValue(role.image, root);
            const imageSrc = escapeAttribute(option && option.src ? option.src : '');
            const answerLanguage = getAnswerLanguageLabel(
                normalizeAnswerLanguageSetting(role.answerLanguage || SETTINGS_DEFAULTS.answerLanguage),
                root
            );
            const defaultModel = normalizePreferredModel(role.defaultModel)
                || getSettingsText('settings_custom_roles_default_model_inherit', root, 'Browser default model');
            const defaultStyle = normalizeCustomRoleDefaultStyle(role.defaultStyle)
                ? getSettingsText('style_' + normalizeCustomRoleDefaultStyle(role.defaultStyle), root, role.defaultStyle)
                : getSettingsText('settings_custom_roles_default_style_inherit', root, 'Global response style');
            return ''
                + '<article class="custom-role-card">'
                + '  <div class="custom-role-card-main">'
                + '    <img class="custom-role-card-image" src="' + imageSrc + '" alt="' + escapeAttribute(role.name) + '">'
                + '    <div class="custom-role-card-copy">'
                + '      <div class="custom-role-card-name">' + escapeHtml(role.name) + '</div>'
                + '      <div class="custom-role-card-meta">' + escapeHtml(answerLanguage) + '</div>'
                + '      <div class="custom-role-card-meta">' + escapeHtml(defaultModel) + '</div>'
                + '      <div class="custom-role-card-meta">' + escapeHtml(defaultStyle) + '</div>'
                + '      <div class="custom-role-card-description">' + escapeHtml(role.description || '') + '</div>'
                + '    </div>'
                + '  </div>'
                + '  <div class="custom-role-card-actions">'
                + '    <button type="button" class="outline" data-custom-role-action="edit" data-custom-role-id="' + escapeAttribute(role.id) + '">'
                +         escapeHtml(getSettingsText('settings_custom_roles_edit', root, 'Edit'))
                + '    </button>'
                + '    <button type="button" class="outline" data-custom-role-action="delete" data-custom-role-id="' + escapeAttribute(role.id) + '">'
                +         escapeHtml(getSettingsText('settings_custom_roles_delete', root, 'Delete'))
                + '    </button>'
                + '  </div>'
                + '</article>';
        }).join('');
    }

    function upsertCustomRoleFromEditor(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const draft = getDraftCustomRoles(root);
        const role = getCurrentCustomRoleFormData(root);
        if (!role.name) {
            if (typeof showAlert === 'function') {
                showAlert(getSettingsText('settings_custom_roles_name_required', root, 'Enter a role name.'), 'error', 3500);
            }
            return false;
        }
        if (!role.prompt) {
            if (typeof showAlert === 'function') {
                showAlert(getSettingsText('settings_custom_roles_prompt_required', root, 'Enter a master prompt for the role.'), 'error', 3500);
            }
            return false;
        }
        const targetId = buildCustomRoleId(role.name, role.id);
        const nextRole = {
            id: targetId,
            name: role.name,
            description: role.description,
            prompt: role.prompt,
            image: role.image,
            answerLanguage: role.answerLanguage,
            defaultModel: role.defaultModel,
            defaultStyle: role.defaultStyle
        };
        const existingIndex = draft.findIndex(function (entry) {
            return entry.id === targetId || (role.id && entry.id === role.id);
        });
        if (existingIndex >= 0) {
            draft[existingIndex] = nextRole;
        } else {
            draft.push(nextRole);
        }
        setDraftCustomRoles(draft, root);
        renderCustomRoleList(root);
        populateCustomRoleEditor(getDraftCustomRoles(root).find(function (entry) { return entry.id === targetId; }), root);
        if (typeof showAlert === 'function') {
            showAlert(getSettingsText('settings_custom_roles_saved', root, 'Role saved.'), 'info', 2500);
        }
        return true;
    }

    function deleteCustomRole(roleId, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const targetId = normalizeRoleId(roleId);
        const draft = getDraftCustomRoles(root);
        const role = draft.find(function (entry) { return entry.id === targetId; });
        if (!role) {
            return;
        }
        const message = getSettingsText('settings_custom_roles_delete_confirm', root, 'Delete role "{name}"?')
            .replace('{name}', role.name || targetId);
        if (!window.confirm(message)) {
            return;
        }
        const remaining = draft.filter(function (entry) {
            return entry.id !== targetId;
        });
        setDraftCustomRoles(remaining, root);
        renderCustomRoleList(root);
        const hidden = root.querySelector('#role-hidden') || document.getElementById('role-hidden');
        if (hidden && hidden.value === targetId) {
            hidden.value = 'analyst';
        }
        clearCustomRoleEditor(root);
        if (typeof showAlert === 'function') {
            showAlert(getSettingsText('settings_custom_roles_deleted', root, 'Role deleted.'), 'info', 2500);
        }
    }

    function applyPreferredModel(settings, scope, roleDefinition) {
        const root = scope instanceof HTMLElement ? scope : document;
        const modelEl = root.querySelector('#model') || document.getElementById('model');
        if (!modelEl || modelEl.disabled) {
            return;
        }
        const targetModel = getResolvedModelForRole(roleDefinition || null, settings, root);
        if (!targetModel) {
            return;
        }
        if (modelEl.value !== targetModel) {
            modelEl.value = targetModel;
            syncModel(root);
        }
    }

    function formatBytes(bytes) {
        const value = Number(bytes);
        if (!Number.isFinite(value) || value <= 0) {
            return '';
        }
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = value;
        let idx = 0;
        while (size >= 1024 && idx < units.length - 1) {
            size /= 1024;
            idx += 1;
        }
        const fractionDigits = size >= 10 || idx === 0 ? 0 : 1;
        return size.toFixed(fractionDigits) + ' ' + units[idx];
    }

    function formatDateTime(value, scope) {
        if (!value) {
            return '';
        }
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) {
            return '';
        }
        try {
            return new Intl.DateTimeFormat(getCurrentLang(scope), {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(parsed);
        } catch (_) {
            return parsed.toISOString();
        }
    }

    function escapeAttribute(value) {
        return escapeHtml(value).replaceAll('`', '&#96;');
    }

    function refreshModelSelect() {
        if (!window.htmx) {
            return;
        }
        const modelEl = document.getElementById('model');
        if (modelEl) {
            window.htmx.trigger(modelEl, 'refreshModels');
        }
    }

    function clearModelManagerPoll() {
        if (modelManagerPollHandle) {
            window.clearTimeout(modelManagerPollHandle);
            modelManagerPollHandle = null;
        }
    }

    function scheduleModelManagerPoll(scope) {
        clearModelManagerPoll();
        modelManagerPollHandle = window.setTimeout(function () {
            loadModelManager(scope || document, { silent: true });
        }, MODEL_MANAGER_POLL_MS);
    }

    function clearEmbeddingModelManagerPoll() {
        if (embeddingModelManagerPollHandle) {
            window.clearTimeout(embeddingModelManagerPollHandle);
            embeddingModelManagerPollHandle = null;
        }
    }

    function scheduleEmbeddingModelManagerPoll(scope) {
        clearEmbeddingModelManagerPoll();
        embeddingModelManagerPollHandle = window.setTimeout(function () {
            loadEmbeddingModelManager(scope || document, { silent: true });
        }, EMBEDDING_MODEL_MANAGER_POLL_MS);
    }

    function renderPullStatus(pullState, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const container = root.querySelector('#models-pull-status') || document.getElementById('models-pull-status');
        if (!container) {
            return;
        }
        const pull = pullState && typeof pullState === 'object' ? pullState : {};
        const status = String(pull.status || 'idle').trim().toLowerCase();
        const shouldShow = !!(pull.active || ['starting', 'pulling', 'success', 'completed', 'error'].includes(status));
        if (!shouldShow) {
            container.hidden = true;
            container.innerHTML = '';
            return;
        }
        const modelName = escapeHtml(String(pull.model || ''));
        const label = escapeHtml(String(pull.label || pull.status || ''));
        const completed = Number(pull.completed);
        const total = Number(pull.total);
        const hasProgress = Number.isFinite(completed) && Number.isFinite(total) && total > 0;
        const progress = hasProgress ? Math.max(0, Math.min(100, Math.round((completed / total) * 100))) : null;
        let progressLabel = '';
        let progressWidth = progress === null ? 32 : progress;
        if (status === 'success' || status === 'completed') {
            progressLabel = escapeHtml(getModelText('models_pull_completed', root, 'Download complete'));
            progressWidth = 100;
        } else if (status === 'error') {
            progressLabel = escapeHtml(getModelText('models_status', root, 'Status'));
            progressWidth = 100;
        } else if (progress === null) {
            progressLabel = escapeHtml(getModelText('models_pull_active', root, 'Downloading'));
        } else {
            progressLabel = progress + '%';
        }
        container.hidden = false;
        container.innerHTML =
            '<div class="models-pull-head">'
            + '<span>' + label + (modelName ? ' · <code>' + modelName + '</code>' : '') + '</span>'
            + '<span>' + progressLabel + '</span>'
            + '</div>'
            + '<div class="models-pull-progress"><div class="models-pull-progress-bar" style="width:'
            + progressWidth
            + '%"></div></div>';
    }

    function buildModelMetaItems(model, scope) {
        const details = model && typeof model.details === 'object' ? model.details : {};
        const items = [];
        const sizeLabel = formatBytes(model ? model.size : 0);
        if (sizeLabel) {
            items.push(getModelText('models_size', scope, 'Size') + ': ' + sizeLabel);
        }
        if (details.parameter_size) {
            items.push(getModelText('models_params', scope, 'Parameters') + ': ' + details.parameter_size);
        }
        if (details.family) {
            items.push(getModelText('models_family', scope, 'Family') + ': ' + details.family);
        }
        if (details.quantization_level) {
            items.push(getModelText('models_quantization', scope, 'Quantization') + ': ' + details.quantization_level);
        }
        const added = formatDateTime(model ? model.modified_at : '', scope);
        if (added) {
            items.push(getModelText('models_added', scope, 'Added') + ': ' + added);
        }
        return items;
    }

    function renderInstalledModels(payload, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const container = root.querySelector('#installed-models-list') || document.getElementById('installed-models-list');
        if (!container) {
            return;
        }
        const data = payload && typeof payload === 'object' ? payload : {};
        const models = Array.isArray(data.installed) ? data.installed : [];
        const settings = normalizeSettings(getSettings());
        const preferredModel = normalizePreferredModel(settings.preferredModel);
        const activeDefault = preferredModel || String(data.default_model || '');
        const pullState = data.pull && typeof data.pull === 'object' ? data.pull : {};
        const pullBusy = !!pullState.active;

        if (!models.length) {
            container.innerHTML = '<p class="muted models-empty">' + escapeHtml(getModelText('models_no_installed', root, 'No installed models yet.')) + '</p>';
            return;
        }

        container.innerHTML = models.map(function (model) {
            const modelName = String(model.name || '');
            const isDefault = activeDefault === modelName;
            const metaItems = buildModelMetaItems(model, root)
                .map(function (item) {
                    return '<span class="model-meta-item">' + escapeHtml(item) + '</span>';
                })
                .join('');
            const badges = isDefault
                ? '<span class="model-badge">' + escapeHtml(getModelText('models_default_badge', root, 'Default')) + '</span>'
                : '';
            return ''
                + '<article class="model-card">'
                + '  <div class="model-card-head">'
                + '    <div class="model-card-title"><strong><code>' + escapeHtml(modelName) + '</code></strong></div>'
                + '    <div class="model-badges">' + badges + '</div>'
                + '  </div>'
                + '  <div class="model-card-meta">' + metaItems + '</div>'
                + '  <div class="model-card-actions">'
                + '    <button type="button" class="' + (isDefault ? 'outline' : 'primary') + '" data-model-action="set-default-model" data-model-name="' + escapeAttribute(modelName) + '">'
                +         escapeHtml(isDefault ? getModelText('models_default_active', root, 'Default in this browser') : getModelText('models_use_default', root, 'Use by default'))
                + '    </button>'
                + '    <button type="button" class="outline" data-model-action="delete-model" data-model-name="' + escapeAttribute(modelName) + '"' + (pullBusy ? ' disabled' : '') + '>'
                +         escapeHtml(getModelText('models_delete_button', root, 'Delete'))
                + '    </button>'
                + '  </div>'
                + '</article>';
        }).join('');
    }

    function renderRecommendedModels(payload, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const container = root.querySelector('#recommended-models-list') || document.getElementById('recommended-models-list');
        if (!container) {
            return;
        }
        const data = payload && typeof payload === 'object' ? payload : {};
        const settings = normalizeSettings(getSettings());
        const effectiveAnswerLanguage = getEffectiveAnswerLanguage(settings.answerLanguage, root);
        const policyOrder = getModelPolicyOrder(effectiveAnswerLanguage);
        const models = (Array.isArray(data.recommended) ? data.recommended : []).slice().sort(function (left, right) {
            const leftIndex = policyOrder.indexOf(String(left && left.name || ''));
            const rightIndex = policyOrder.indexOf(String(right && right.name || ''));
            const safeLeft = leftIndex === -1 ? 999 : leftIndex;
            const safeRight = rightIndex === -1 ? 999 : rightIndex;
            if (safeLeft !== safeRight) {
                return safeLeft - safeRight;
            }
            return String(left && left.name || '').localeCompare(String(right && right.name || ''));
        });
        const installedNames = new Set((Array.isArray(data.installed) ? data.installed : []).map(function (item) {
            return String(item.name || '');
        }));
        const pullState = data.pull && typeof data.pull === 'object' ? data.pull : {};
        const activePullModel = String(pullState.model || '');

        if (!models.length) {
            container.innerHTML = '<p class="muted models-empty">' + escapeHtml(getModelText('models_no_recommended', root, 'No recommended models.')) + '</p>';
            return;
        }

        container.innerHTML = models.map(function (item) {
            const modelName = String(item.name || '');
            const isInstalled = installedNames.has(modelName);
            const isActivePull = !!pullState.active && activePullModel === modelName;
            const badges = [];
            if (policyOrder[0] === modelName) {
                badges.push('<span class="model-badge">' + escapeHtml(getModelText('models_recommended_for_language', root, 'Top pick for {language}').replace('{language}', getAnswerLanguageLabel(effectiveAnswerLanguage, root))) + '</span>');
            }
            if (isInstalled) {
                badges.push('<span class="model-badge is-installed">' + escapeHtml(getModelText('models_installed_badge', root, 'Installed')) + '</span>');
            }
            const actionButton = isInstalled
                ? ''
                : '<button type="button" class="primary" data-model-action="pull-model" data-model-name="' + escapeAttribute(modelName) + '"' + (pullState.active ? ' disabled' : '') + '>'
                    + escapeHtml(isActivePull ? getModelText('models_pull_active', root, 'Downloading') : getModelText('models_pull_button', root, 'Download'))
                    + '</button>';
            return ''
                + '<article class="model-card">'
                + '  <div class="model-card-head">'
                + '    <div class="model-card-title">'
                + '      <strong><code>' + escapeHtml(modelName) + '</code></strong>'
                + '      <span class="model-card-summary">' + escapeHtml(String(item.summary || '')) + '</span>'
                + '    </div>'
                + '    <div class="model-badges">' + badges.join('') + '</div>'
                + '  </div>'
                + '  <div class="model-card-actions">' + actionButton + '</div>'
                + '</article>';
        }).join('');
    }

    function renderModelManager(payload, scope) {
        lastModelManagerPayload = payload;
        renderInstalledModels(payload, scope);
        renderRecommendedModels(payload, scope);
        renderPullStatus(payload && payload.pull ? payload.pull : {}, scope);
    }

    function renderEmbeddingPullStatus(pullState, scope) {
        const container = getEmbeddingModelsStatus(scope);
        if (!container) {
            return;
        }
        const pull = pullState && typeof pullState === 'object' ? pullState : {};
        const status = String(pull.status || 'idle').trim().toLowerCase();
        const shouldShow = !!(pull.active || ['starting', 'loading', 'success', 'completed', 'error'].includes(status));
        if (!shouldShow) {
            container.hidden = true;
            container.innerHTML = '';
            return;
        }
        const modelName = escapeHtml(String(pull.model || ''));
        const label = escapeHtml(String(pull.label || pull.status || ''));
        const progressLabel = status === 'success' || status === 'completed'
            ? escapeHtml(getSettingsText('embedding_models_prepare_status_success', scope, 'Embedding model is ready.'))
            : (status === 'error'
                ? escapeHtml(getSettingsText('embedding_models_prepare_status_error', scope, 'Failed to prepare embedding model: {error}').replace('{error}', String(pull.error || '-')))
                : escapeHtml(getSettingsText('embedding_models_prepare_status_loading', scope, 'Preparing embedding model...')));
        const progressWidth = status === 'error' || status === 'success' || status === 'completed' ? 100 : 48;
        container.hidden = false;
        container.innerHTML =
            '<div class="models-pull-head">'
            + '<span>' + label + (modelName ? ' · <code>' + modelName + '</code>' : '') + '</span>'
            + '<span>' + progressLabel + '</span>'
            + '</div>'
            + '<div class="models-pull-progress"><div class="models-pull-progress-bar" style="width:'
            + progressWidth
            + '%"></div></div>';
    }

    function renderInstalledEmbeddingModels(payload, scope) {
        const container = getInstalledEmbeddingModelsList(scope);
        if (!container) {
            return;
        }
        const data = payload && typeof payload === 'object' ? payload : {};
        const currentModel = String(data.current_model || '').trim();
        const models = Array.isArray(data.available) ? data.available : [];

        if (!models.length) {
            container.innerHTML = '<p class="muted models-empty">' + escapeHtml(getSettingsText('embedding_models_no_available', scope, 'No prepared embedding models yet.')) + '</p>';
            return;
        }

        container.innerHTML = models.map(function (item) {
            const modelName = String(item && item.name || '');
            const source = String(item && item.source || '');
            const badges = [];
            if (modelName === currentModel) {
                badges.push('<span class="model-badge">' + escapeHtml(getSettingsText('embedding_models_current_badge', scope, 'Current')) + '</span>');
            }
            badges.push('<span class="model-badge is-installed">' + escapeHtml(getSettingsText('embedding_models_cached_badge', scope, 'Ready')) + '</span>');
            if (source === 'local_path') {
                badges.push('<span class="model-badge">' + escapeHtml(getSettingsText('embedding_models_local_path_badge', scope, 'Local path')) + '</span>');
            }
            return ''
                + '<article class="model-card">'
                + '  <div class="model-card-head">'
                + '    <div class="model-card-title"><strong><code>' + escapeHtml(modelName) + '</code></strong></div>'
                + '    <div class="model-badges">' + badges.join('') + '</div>'
                + '  </div>'
                + '  <div class="model-card-actions">'
                + '    <button type="button" class="primary" data-embedding-model-action="use" data-embedding-model-name="' + escapeAttribute(modelName) + '">'
                +         escapeHtml(getSettingsText('embedding_models_use_button', scope, 'Use'))
                + '    </button>'
                + '  </div>'
                + '</article>';
        }).join('');
    }

    function renderRecommendedEmbeddingModels(payload, scope) {
        const container = getRecommendedEmbeddingModelsList(scope);
        if (!container) {
            return;
        }
        const data = payload && typeof payload === 'object' ? payload : {};
        const currentModel = String(data.current_model || '').trim();
        const pullState = data.pull && typeof data.pull === 'object' ? data.pull : {};
        const activePullModel = String(pullState.model || '').trim();
        const models = Array.isArray(data.recommended) ? data.recommended : [];

        if (!models.length) {
            container.innerHTML = '<p class="muted models-empty">' + escapeHtml(getSettingsText('embedding_models_no_recommended', scope, 'No recommended embedding models.')) + '</p>';
            return;
        }

        container.innerHTML = models.map(function (item) {
            const modelName = String(item && item.name || '');
            const available = !!(item && item.available);
            const badges = [];
            if (available) {
                badges.push('<span class="model-badge is-installed">' + escapeHtml(getSettingsText('embedding_models_cached_badge', scope, 'Ready')) + '</span>');
            }
            if (modelName === currentModel) {
                badges.push('<span class="model-badge">' + escapeHtml(getSettingsText('embedding_models_current_badge', scope, 'Current')) + '</span>');
            }
            const actionLabel = available
                ? getSettingsText('embedding_models_use_button', scope, 'Use')
                : (pullState.active && activePullModel === modelName
                    ? getSettingsText('embedding_models_prepare_status_loading', scope, 'Preparing embedding model...')
                    : getSettingsText('embedding_models_prepare_button', scope, 'Download / check'));
            const action = available ? 'use' : 'prepare';
            return ''
                + '<article class="model-card">'
                + '  <div class="model-card-head">'
                + '    <div class="model-card-title">'
                + '      <strong><code>' + escapeHtml(modelName) + '</code></strong>'
                + '      <span class="model-card-summary">' + escapeHtml(String(item && item.summary || '')) + '</span>'
                + '    </div>'
                + '    <div class="model-badges">' + badges.join('') + '</div>'
                + '  </div>'
                + '  <div class="model-card-actions">'
                + '    <button type="button" class="' + (available ? 'outline' : 'primary') + '" data-embedding-model-action="' + action + '" data-embedding-model-name="' + escapeAttribute(modelName) + '"' + ((!available && pullState.active) ? ' disabled' : '') + '>'
                +         escapeHtml(actionLabel)
                + '    </button>'
                + '  </div>'
                + '</article>';
        }).join('');
    }

    function renderEmbeddingModelManager(payload, scope) {
        lastEmbeddingModelManagerPayload = payload;
        renderInstalledEmbeddingModels(payload, scope);
        renderRecommendedEmbeddingModels(payload, scope);
        renderEmbeddingPullStatus(payload && payload.pull ? payload.pull : {}, scope);
    }

    function applyPreferredModelSetting(modelName, scope) {
        const settings = normalizeSettings(getSettings());
        settings.preferredModel = normalizePreferredModel(modelName);
        window.LocalRagSettings = settings;
        saveSettings(settings);
        applyPreferredModel(settings, scope || document);
        syncModel(scope || document);
        updateAskState();
        markResponseStale();
        if (lastModelManagerPayload) {
            renderModelManager(lastModelManagerPayload, scope || document);
        }
    }

    function clearPreferredModelIfMatches(modelName, scope) {
        const settings = normalizeSettings(getSettings());
        if (normalizePreferredModel(settings.preferredModel) !== normalizePreferredModel(modelName)) {
            return;
        }
        settings.preferredModel = '';
        window.LocalRagSettings = settings;
        saveSettings(settings);
        applyPreferredModel(settings, scope || document);
        syncModel(scope || document);
    }

    async function fetchJson(url, options) {
        const response = await window.fetch(url, Object.assign({
            headers: { 'Accept': 'application/json' },
            credentials: 'same-origin'
        }, options || {}));
        const payload = await response.json();
        if (!response.ok) {
            const message = payload && payload.message ? payload.message : response.statusText;
            throw new Error(message || 'Request failed');
        }
        return payload;
    }

    function downloadJsonFile(filename, content) {
        const blob = new Blob([content], { type: 'application/json;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }

    async function loadServerCustomRoles(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const payload = await fetchJson('/api/profile/custom-roles');
        return setServerProfile({ custom_roles: payload.custom_roles }, root).customRoles;
    }

    async function saveServerCustomRoles(roles, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const payload = await fetchJson('/api/profile/custom-roles', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                custom_roles: normalizeCustomRoles(roles, root)
            })
        });
        return setServerProfile({ custom_roles: payload.custom_roles }, root).customRoles;
    }

    async function exportServerCustomRoles(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const payload = await fetchJson('/api/profile/custom-roles/export');
        const customRoles = normalizeCustomRoles(payload.custom_roles, root);
        downloadJsonFile(
            'localrag-custom-roles.json',
            JSON.stringify({ custom_roles: customRoles }, null, 2) + '\n'
        );
        return customRoles;
    }

    async function importServerCustomRoles(file, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const rawText = await file.text();
        let parsed = null;
        try {
            parsed = JSON.parse(rawText);
        } catch (_) {
            throw new Error(getSettingsText('settings_custom_roles_import_invalid', root, 'Invalid custom roles JSON.'));
        }
        const rawRoles = Array.isArray(parsed)
            ? parsed
            : (parsed && typeof parsed === 'object' ? (parsed.custom_roles || parsed.customRoles) : null);
        if (!Array.isArray(rawRoles)) {
            throw new Error(getSettingsText('settings_custom_roles_import_invalid', root, 'Invalid custom roles JSON.'));
        }
        const customRoles = await saveServerCustomRoles(rawRoles, root);
        return syncServerCustomRolesToSettings(customRoles, root);
    }

    async function resetServerCustomRoles(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const customRoles = await saveServerCustomRoles([], root);
        return syncServerCustomRolesToSettings(customRoles, root);
    }

    function closeDocsBrowser(scope) {
        const overlay = getDocsBrowserOverlay(scope);
        const card = getDocsBrowserCard(scope);
        const search = getDocsBrowserSearch(scope);
        if (!card) {
            return;
        }
        if (overlay) {
            overlay.hidden = true;
        }
        card.hidden = true;
        card.dataset.currentPath = '';
        card.dataset.parentPath = '';
        lastDocsBrowserPayload = null;
        if (search) {
            search.value = '';
        }
    }

    function renderDocsBrowser(payload, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const card = getDocsBrowserCard(root);
        const current = getDocsBrowserCurrent(root);
        const list = getDocsBrowserList(root);
        const upButton = getDocsBrowserUpButton(root);
        const searchInput = getDocsBrowserSearch(root);
        if (!card || !current || !list) {
            return;
        }

        const currentPath = payload && payload.path ? String(payload.path) : '';
        const parentPath = payload && payload.parent_path ? String(payload.parent_path) : '';
        const directories = payload && Array.isArray(payload.directories) ? payload.directories : [];
        const searchTerm = searchInput ? String(searchInput.value || '').trim().toLowerCase() : '';
        const filteredDirectories = !searchTerm
            ? directories
            : directories.filter(function (entry) {
                const name = String((entry && entry.name) || '').toLowerCase();
                const pathValue = String((entry && entry.path) || '').toLowerCase();
                return name.includes(searchTerm) || pathValue.includes(searchTerm);
            });

        card.hidden = false;
        card.dataset.currentPath = currentPath;
        card.dataset.parentPath = parentPath;
        current.textContent = currentPath;
        lastDocsBrowserPayload = payload || null;
        if (upButton) {
            upButton.disabled = !parentPath;
        }

        list.innerHTML = '';
        if (!filteredDirectories.length) {
            const empty = document.createElement('p');
            empty.className = 'muted docs-browser-empty';
            empty.textContent = getDocsBrowserEmptyMessage();
            list.appendChild(empty);
            return;
        }

        filteredDirectories.forEach(function (entry) {
            const targetPath = String((entry && entry.path) || '').trim();
            const name = String((entry && entry.name) || '').trim() || targetPath;
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'docs-browser-item';
            button.setAttribute('data-docs-browser-path', targetPath);

            const icon = document.createElement('span');
            icon.className = 'docs-browser-item-icon';
            icon.textContent = 'DIR';

            const copy = document.createElement('span');
            copy.className = 'docs-browser-item-copy';

            const title = document.createElement('span');
            title.className = 'docs-browser-item-name';
            title.textContent = name;

            const pathLabel = document.createElement('span');
            pathLabel.className = 'docs-browser-item-path';
            pathLabel.textContent = targetPath;

            copy.appendChild(title);
            copy.appendChild(pathLabel);
            button.appendChild(icon);
            button.appendChild(copy);
            list.appendChild(button);
        });
    }

    async function loadDocsBrowser(pathValue, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const overlay = getDocsBrowserOverlay(root);
        const card = getDocsBrowserCard(root);
        const list = getDocsBrowserList(root);
        if (!card || !list) {
            return;
        }

        if (overlay) {
            overlay.hidden = false;
        }
        card.hidden = false;
        list.innerHTML = '<p class="muted docs-browser-empty">' + escapeHtml(getDocsBrowserLoadingMessage()) + '</p>';

        const rawPath = String(pathValue || '').trim();
        const url = rawPath ? '/api/fs/dirs?path=' + encodeURIComponent(rawPath) : '/api/fs/dirs';
        try {
            const payload = await fetchJson(url);
            renderDocsBrowser(payload, root);
        } catch (error) {
            const message = error instanceof Error ? error.message : getDocsBrowserErrorMessage();
            list.innerHTML = '<p class="muted docs-browser-empty">' + escapeHtml(message) + '</p>';
            if (typeof showAlert === 'function') {
                showAlert(message, 'error', 4500);
            }
        }
    }

    async function updateDocsPathRequest(pathValue, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const docsPath = String(pathValue || '').trim();
        if (!docsPath) {
            throw new Error(getDocsInvalidPathMessage());
        }
        const payload = await fetchJson('/api/docs-path', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ docs_path: docsPath })
        });
        const input = getDocsPathInput(root);
        if (input && payload && payload.docs_path) {
            input.value = payload.docs_path;
            input.dataset.currentValue = payload.docs_path;
        }
        if (window.htmx) {
            const statusCard = document.getElementById('status-card');
            if (statusCard) {
                window.htmx.trigger(statusCard, 'refreshStatus');
            }
        }
        if (window.startStatusPolling) {
            window.startStatusPolling();
        }
        if (typeof showAlert === 'function') {
            showAlert(
                getDocsPathUpdatedMessage(payload && payload.docs_path ? payload.docs_path : docsPath),
                'info',
                3500
            );
        }
        return payload;
    }

    async function updateRuntimeConfigRequest(config, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const payload = config && typeof config === 'object' ? config : {};
        const requestBody = {};

        if (Object.prototype.hasOwnProperty.call(payload, 'docsPath')) {
            const docsPath = String(payload.docsPath || '').trim();
            if (!docsPath) {
                throw new Error(getDocsInvalidPathMessage());
            }
            requestBody.docs_path = docsPath;
        }

        if (Object.prototype.hasOwnProperty.call(payload, 'embeddingModel')) {
            const embeddingModel = String(payload.embeddingModel || '').trim();
            if (!embeddingModel) {
                throw new Error(
                    getSettingsText('settings_embedding_model_invalid', root, 'Enter an embedding model.')
                );
            }
            requestBody.embedding_model = embeddingModel;
        }

        const responsePayload = await fetchJson('/api/runtime-config', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const docsPathInput = getDocsPathInput(root);
        if (docsPathInput && responsePayload && responsePayload.docs_path) {
            docsPathInput.value = responsePayload.docs_path;
            docsPathInput.dataset.currentValue = responsePayload.docs_path;
        }

        if (responsePayload && responsePayload.embedding_model) {
            setCurrentEmbeddingModel(root, responsePayload.embedding_model);
            setEmbeddingModelControls(responsePayload.embedding_model, root);
            loadEmbeddingModelManager(root, { silent: true });
        }

        if (window.htmx) {
            const statusCard = document.getElementById('status-card');
            if (statusCard) {
                window.htmx.trigger(statusCard, 'refreshStatus');
            }
        }

        if (responsePayload && responsePayload.changed && window.startStatusPolling) {
            window.startStatusPolling();
        }

        if (typeof showAlert === 'function' && responsePayload && responsePayload.message) {
            showAlert(responsePayload.message, 'info', 4500);
        }
        return responsePayload;
    }

    async function loadModelManager(scope, options) {
        const root = scope instanceof HTMLElement ? scope : document;
        const installed = root.querySelector('#installed-models-list') || document.getElementById('installed-models-list');
        const recommended = root.querySelector('#recommended-models-list') || document.getElementById('recommended-models-list');
        const config = options && typeof options === 'object' ? options : {};
        const previousPull = lastModelManagerPayload && lastModelManagerPayload.pull
            ? Object.assign({}, lastModelManagerPayload.pull)
            : null;
        if (!installed || !recommended) {
            return;
        }
        if (!config.silent) {
            const loadingText = escapeHtml(getLoadingMessage());
            installed.innerHTML = '<p class="muted models-empty">' + loadingText + '</p>';
            recommended.innerHTML = '<p class="muted models-empty">' + loadingText + '</p>';
        }
        try {
            const payload = await fetchJson('/api/models/data');
            renderModelManager(payload, root);
            if (previousPull && previousPull.active && payload.pull && !payload.pull.active) {
                refreshModelSelect();
            }
            if (payload.pull && payload.pull.active) {
                scheduleModelManagerPoll(root);
            } else {
                clearModelManagerPoll();
            }
        } catch (error) {
            clearModelManagerPoll();
            const message = error instanceof Error ? error.message : getModelText('models_unavailable', root, 'Models unavailable');
            installed.innerHTML = '<p class="muted models-empty">' + escapeHtml(message) + '</p>';
            recommended.innerHTML = '<p class="muted models-empty">' + escapeHtml(getModelText('models_no_recommended', root, 'No recommended models.')) + '</p>';
            renderPullStatus({}, root);
        }
    }

    async function loadEmbeddingModelManager(scope, options) {
        const root = scope instanceof HTMLElement ? scope : document;
        const installed = getInstalledEmbeddingModelsList(root);
        const recommended = getRecommendedEmbeddingModelsList(root);
        const config = options && typeof options === 'object' ? options : {};
        const previousPull = lastEmbeddingModelManagerPayload && typeof lastEmbeddingModelManagerPayload === 'object'
            ? lastEmbeddingModelManagerPayload.pull
            : null;
        if (!installed || !recommended) {
            return;
        }
        if (!config.silent) {
            const loadingText = escapeHtml(getLoadingMessage());
            installed.innerHTML = '<p class="muted models-empty">' + loadingText + '</p>';
            recommended.innerHTML = '<p class="muted models-empty">' + loadingText + '</p>';
        }
        try {
            const payload = await fetchJson('/api/embedding-models/data');
            renderEmbeddingModelManager(payload, root);
            if (previousPull && previousPull.active && payload.pull && !payload.pull.active) {
                // Refresh availability badges after the background prepare finishes.
                renderEmbeddingModelManager(payload, root);
            }
            if (payload.pull && payload.pull.active) {
                scheduleEmbeddingModelManagerPoll(root);
            } else {
                clearEmbeddingModelManagerPoll();
            }
        } catch (error) {
            clearEmbeddingModelManagerPoll();
            const message = error instanceof Error ? error.message : getSettingsText('embedding_models_no_available', root, 'No prepared embedding models yet.');
            installed.innerHTML = '<p class="muted models-empty">' + escapeHtml(message) + '</p>';
            recommended.innerHTML = '<p class="muted models-empty">' + escapeHtml(getSettingsText('embedding_models_no_recommended', root, 'No recommended embedding models.')) + '</p>';
            renderEmbeddingPullStatus({}, root);
        }
    }

    async function startModelPullRequest(modelName, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        try {
            const payload = await fetchJson('/api/models/pull', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ model: modelName })
            });
            if (typeof showAlert === 'function') {
                showAlert(payload.message || getModelText('models_pull_button', root, 'Download'), 'info', 3500);
            }
            await loadModelManager(root, { silent: true });
            return true;
        } catch (error) {
            if (typeof showAlert === 'function') {
                showAlert(error instanceof Error ? error.message : String(error), 'error', 5000);
            }
            return false;
        }
    }

    async function startEmbeddingModelPullRequest(modelName, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const target = String(modelName || '').trim();
        if (!target) {
            if (typeof showAlert === 'function') {
                showAlert(getSettingsText('embedding_models_invalid_name', root, 'Enter an embedding model or local path.'), 'error', 4500);
            }
            return;
        }
        try {
            const payload = await fetchJson('/api/embedding-models/pull', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ embedding_model: target })
            });
            if (typeof showAlert === 'function') {
                showAlert(payload.message || getSettingsText('embedding_models_prepare_button', root, 'Download / check'), 'info', 3500);
            }
            await loadEmbeddingModelManager(root, { silent: true });
        } catch (error) {
            if (typeof showAlert === 'function') {
                showAlert(error instanceof Error ? error.message : String(error), 'error', 5000);
            }
        }
    }

    async function deleteModelRequest(modelName, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const confirmMessage = getModelText('models_delete_confirm', root, 'Delete model {model}?').replace('{model}', modelName);
        if (window.confirm && !window.confirm(confirmMessage)) {
            return;
        }
        try {
            const payload = await fetchJson('/api/models/delete', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin',
                body: JSON.stringify({ model: modelName })
            });
            clearPreferredModelIfMatches(modelName, root);
            refreshModelSelect();
            await loadModelManager(root, { silent: true });
            if (typeof showAlert === 'function') {
                showAlert(payload.message || getModelText('models_delete_button', root, 'Delete'), 'info', 3500);
            }
        } catch (error) {
            if (typeof showAlert === 'function') {
                showAlert(error instanceof Error ? error.message : String(error), 'error', 5000);
            }
        }
    }

    function applySettingsToUi(settings, scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const safe = normalizeSettings(settings);
        const rolePrompts = getRolePromptsForScope(safe, root);
        const effectiveAnswerLanguage = getEffectiveAnswerLanguage(safe.answerLanguage, root);
        const currentEmbeddingModel = getCurrentEmbeddingModel(root);

        const historyLimitHidden = root.querySelector('#history-limit-hidden') || document.getElementById('history-limit-hidden');
        const answerLanguageHidden = root.querySelector('#answer-language-hidden') || document.getElementById('answer-language-hidden');
        const roleStyleHidden = root.querySelector('#role-style-hidden') || document.getElementById('role-style-hidden');
        const debugModeHidden = root.querySelector('#debug-mode-hidden') || document.getElementById('debug-mode-hidden');

        if (historyLimitHidden) {
            historyLimitHidden.value = String(safe.historyLimit);
        }
        if (answerLanguageHidden) {
            answerLanguageHidden.value = effectiveAnswerLanguage;
        }
        if (roleStyleHidden) {
            roleStyleHidden.value = safe.roleStyle;
        }
        if (debugModeHidden) {
            debugModeHidden.value = safe.debugMode ? '1' : '0';
        }

        const settingsHistory = root.querySelector('#settings-history-limit') || document.getElementById('settings-history-limit');
        const settingsHistoryValue = root.querySelector('#settings-history-limit-value') || document.getElementById('settings-history-limit-value');
        const settingsAnswerLanguage = root.querySelector('#settings-answer-language') || document.getElementById('settings-answer-language');
        const settingsRoleStyle = root.querySelector('#settings-role-style') || document.getElementById('settings-role-style');
        const settingsDebug = root.querySelector('#settings-debug-mode') || document.getElementById('settings-debug-mode');

        if (settingsHistory) {
            settingsHistory.value = String(safe.historyLimit);
        }
        if (settingsHistoryValue) {
            settingsHistoryValue.textContent = String(safe.historyLimit);
        }
        if (settingsAnswerLanguage) {
            settingsAnswerLanguage.value = safe.answerLanguage;
        }
        if (settingsRoleStyle) {
            settingsRoleStyle.value = safe.roleStyle;
        }
        if (settingsDebug) {
            settingsDebug.checked = safe.debugMode;
        }

        setDraftCustomRoles(safe.customRoles, root);
        renderRoleSelector(safe, root);
        renderCustomRoleList(root);
        refreshCustomRoleDefaultModelSelect(root);
        clearCustomRoleEditor(root);
        setEmbeddingModelControls(currentEmbeddingModel, root);

        ROLE_KEYS.forEach(function (role) {
            const input = getRolePromptInput(role, root);
            if (input) {
                input.value = rolePrompts[role] || '';
            }
        });

        applyRoleImages(safe, root);
        applyPreferredModel(safe, root);
        updateRolePromptScopeLabel(safe.answerLanguage, root);
        syncRole(root, safe);
        updateRoleSelection(root);
        syncCustomRolePrompt(root, safe);
    }

    function collectSettingsFromModal(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const settingsHistory = root.querySelector('#settings-history-limit') || document.getElementById('settings-history-limit');
        const settingsAnswerLanguage = root.querySelector('#settings-answer-language') || document.getElementById('settings-answer-language');
        const settingsRoleStyle = root.querySelector('#settings-role-style') || document.getElementById('settings-role-style');
        const settingsDebug = root.querySelector('#settings-debug-mode') || document.getElementById('settings-debug-mode');
        const answerLanguage = normalizeAnswerLanguageSetting(
            settingsAnswerLanguage ? settingsAnswerLanguage.value : SETTINGS_DEFAULTS.answerLanguage
        );
        const effectiveAnswerLanguage = getEffectiveAnswerLanguage(answerLanguage, root);
        const defaultPrompts = getDefaultRolePrompts(root, effectiveAnswerLanguage);
        const currentSettings = normalizeSettings(getSettings());
        const rolePromptsByLang = Object.assign({}, currentSettings.rolePromptsByLang || {});
        const currentRolePrompts = {};
        const roleImages = {};

        ROLE_KEYS.forEach(function (role) {
            const input = getRolePromptInput(role, root);
            currentRolePrompts[role] = input ? input.value : (defaultPrompts[role] || '');
            roleImages[role] = getRoleImageSelect(role, root)
                ? getRoleImageSelect(role, root).value
                : normalizeRoleImageChoice(role, '', root);
        });

        rolePromptsByLang[effectiveAnswerLanguage] = normalizeRolePromptMap(currentRolePrompts, defaultPrompts);

        return normalizeSettings({
            historyLimit: settingsHistory ? settingsHistory.value : SETTINGS_DEFAULTS.historyLimit,
            answerLanguage: answerLanguage,
            roleStyle: settingsRoleStyle ? settingsRoleStyle.value : SETTINGS_DEFAULTS.roleStyle,
            debugMode: settingsDebug ? settingsDebug.checked : SETTINGS_DEFAULTS.debugMode,
            rolePromptsByLang: rolePromptsByLang,
            roleImages: roleImages,
            customRoles: getDraftCustomRoles(root),
            preferredModel: currentSettings.preferredModel
        });
    }

    function buildResetSettings(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const currentSettings = normalizeSettings(getSettings());
        const effectiveAnswerLanguage = getEffectiveAnswerLanguage(SETTINGS_DEFAULTS.answerLanguage, root);
        const rolePromptsByLang = Object.assign({}, currentSettings.rolePromptsByLang || {});

        rolePromptsByLang[effectiveAnswerLanguage] = getDefaultRolePrompts(root, effectiveAnswerLanguage);

        return normalizeSettings({
            historyLimit: SETTINGS_DEFAULTS.historyLimit,
            answerLanguage: SETTINGS_DEFAULTS.answerLanguage,
            roleStyle: SETTINGS_DEFAULTS.roleStyle,
            debugMode: SETTINGS_DEFAULTS.debugMode,
            rolePromptsByLang: rolePromptsByLang,
            roleImages: getDefaultRoleImages(root),
            customRoles: getServerCustomRoles(root),
            preferredModel: currentSettings.preferredModel
        });
    }

    function openSettingsModal() {
        const modal = document.getElementById('settings-modal');
        if (!modal) {
            return;
        }
        modal.hidden = false;
        document.body.classList.add('modal-open');
        activateSettingsTab(activeSettingsTab, document);
    }

    function closeSettingsModal() {
        const modal = document.getElementById('settings-modal');
        if (!modal) {
            return;
        }
        modal.hidden = true;
        document.body.classList.remove('modal-open');
    }

    function refreshHistoryPanel() {
        if (!window.htmx) {
            return;
        }
        const historyCard = document.getElementById('history-card');
        if (historyCard) {
            window.htmx.trigger(historyCard, 'refreshHistory');
        }
    }

    function bindSettingsModal(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const openBtn = root.querySelector('#settings-open-btn') || document.getElementById('settings-open-btn');
        const closeBtn = root.querySelector('#settings-close-btn') || document.getElementById('settings-close-btn');
        const saveBtn = root.querySelector('#settings-save-btn') || document.getElementById('settings-save-btn');
        const resetBtn = root.querySelector('#settings-reset-btn') || document.getElementById('settings-reset-btn');
        const historySlider = root.querySelector('#settings-history-limit') || document.getElementById('settings-history-limit');
        const historyValue = root.querySelector('#settings-history-limit-value') || document.getElementById('settings-history-limit-value');
        const docsPathInput = getDocsPathInput(root);
        const embeddingModelSelect = getEmbeddingModelSelect(root);
        const embeddingModelCustomInput = getEmbeddingModelCustomInput(root);
        const embeddingModelPrepareBtn = root.querySelector('#embedding-model-prepare-btn') || document.getElementById('embedding-model-prepare-btn');
        const docsPickerBtn = root.querySelector('#settings-docs-picker-btn') || document.getElementById('settings-docs-picker-btn');
        const docsBrowserUpBtn = getDocsBrowserUpButton(root);
        const docsBrowserUseBtn = getDocsBrowserUseButton(root);
        const docsBrowserCloseBtn = getDocsBrowserCloseButton(root);
        const docsBrowserSearch = getDocsBrowserSearch(root);
        const answerLanguageSelect = root.querySelector('#settings-answer-language') || document.getElementById('settings-answer-language');
        const customRoleImageSelect = getCustomRoleImageSelect(root);
        const customRoleDefaultModelSelect = getCustomRoleDefaultModelSelect(root);
        const customRoleDefaultStyleSelect = getCustomRoleDefaultStyleSelect(root);
        const customRolesExportBtn = getCustomRolesExportButton(root);
        const customRolesImportBtn = getCustomRolesImportButton(root);
        const customRolesImportInput = getCustomRolesImportInput(root);
        const customRolesResetBtn = getCustomRolesResetButton(root);
        const customRoleSaveBtn = root.querySelector('#custom-role-save-btn') || document.getElementById('custom-role-save-btn');
        const customRoleClearBtn = root.querySelector('#custom-role-clear-btn') || document.getElementById('custom-role-clear-btn');
        const refreshModelsBtn = root.querySelector('#models-refresh-btn') || document.getElementById('models-refresh-btn');
        const manualModelInput = root.querySelector('#manual-model-name') || document.getElementById('manual-model-name');
        const manualModelPullBtn = root.querySelector('#manual-model-pull-btn') || document.getElementById('manual-model-pull-btn');
        const modal = root.querySelector('#settings-modal') || document.getElementById('settings-modal');
        const backdrop = root.querySelector('[data-settings-close]') || document.querySelector('[data-settings-close]');
        const docsBrowserBackdrop = root.querySelector('[data-docs-browser-close]') || document.querySelector('[data-docs-browser-close]');
        const settingsTabs = getSettingsTabButtons(root);

        if (openBtn && openBtn.dataset.boundSettings !== '1') {
            openBtn.dataset.boundSettings = '1';
            openBtn.addEventListener('click', async function (evt) {
                evt.preventDefault();
                applySettingsToUi(getSettings(), document);
                closeDocsBrowser(document);
                activateSettingsTab(activeSettingsTab, document);
                openSettingsModal();
                loadEmbeddingModelManager(document);
                loadModelManager(document);
                try {
                    const customRoles = await loadServerCustomRoles(document);
                    syncServerCustomRolesToSettings(customRoles, document);
                } catch (_) {
                    // Keep current state if the refresh fails; saving still goes through the server.
                }
            });
        }

        if (closeBtn && closeBtn.dataset.boundSettings !== '1') {
            closeBtn.dataset.boundSettings = '1';
            closeBtn.addEventListener('click', function () {
                closeDocsBrowser(document);
                closeSettingsModal();
            });
        }

        if (backdrop && backdrop.dataset.boundSettings !== '1') {
            backdrop.dataset.boundSettings = '1';
            backdrop.addEventListener('click', function () {
                closeDocsBrowser(document);
                closeSettingsModal();
            });
        }

        if (historySlider && historySlider.dataset.boundSettings !== '1') {
            historySlider.dataset.boundSettings = '1';
            historySlider.addEventListener('input', function () {
                if (historyValue) {
                    historyValue.textContent = historySlider.value;
                }
            });
        }

        if (answerLanguageSelect && answerLanguageSelect.dataset.boundSettings !== '1') {
            answerLanguageSelect.dataset.boundSettings = '1';
            answerLanguageSelect.addEventListener('change', function () {
                const currentSettings = collectSettingsFromModal(document);
                currentSettings.answerLanguage = normalizeAnswerLanguageSetting(answerLanguageSelect.value);
                applySettingsToUi(currentSettings, document);
            });
        }

        if (docsPathInput && !docsPathInput.dataset.currentValue) {
            docsPathInput.dataset.currentValue = docsPathInput.value || '';
        }
        if (embeddingModelSelect && !embeddingModelSelect.dataset.currentValue) {
            embeddingModelSelect.dataset.currentValue = resolveEmbeddingModelSetting(root)
                || embeddingModelSelect.getAttribute('data-current-value')
                || '';
        }
        syncEmbeddingModelInputVisibility(root);

        if (docsPickerBtn && docsPickerBtn.dataset.boundSettings !== '1') {
            docsPickerBtn.dataset.boundSettings = '1';
            docsPickerBtn.addEventListener('click', function () {
                activateSettingsTab('general', document);
                const browser = getDocsBrowserCard(document);
                if (browser && !browser.hidden) {
                    closeDocsBrowser(document);
                    return;
                }
                const startPath = docsPathInput
                    ? String(docsPathInput.value || docsPathInput.dataset.currentValue || docsPathInput.getAttribute('data-default-path') || '').trim()
                    : '';
                loadDocsBrowser(startPath, document);
            });
        }

        if (docsBrowserUpBtn && docsBrowserUpBtn.dataset.boundSettings !== '1') {
            docsBrowserUpBtn.dataset.boundSettings = '1';
            docsBrowserUpBtn.addEventListener('click', function () {
                const browser = getDocsBrowserCard(document);
                const parentPath = browser ? String(browser.dataset.parentPath || '').trim() : '';
                if (!parentPath) {
                    return;
                }
                loadDocsBrowser(parentPath, document);
            });
        }

        if (docsBrowserSearch && docsBrowserSearch.dataset.boundSettings !== '1') {
            docsBrowserSearch.dataset.boundSettings = '1';
            docsBrowserSearch.addEventListener('input', function () {
                if (lastDocsBrowserPayload) {
                    renderDocsBrowser(lastDocsBrowserPayload, document);
                }
            });
        }

        if (docsBrowserUseBtn && docsBrowserUseBtn.dataset.boundSettings !== '1') {
            docsBrowserUseBtn.dataset.boundSettings = '1';
            docsBrowserUseBtn.addEventListener('click', function () {
                const browser = getDocsBrowserCard(document);
                const currentPath = browser ? String(browser.dataset.currentPath || '').trim() : '';
                if (!currentPath || !docsPathInput) {
                    return;
                }
                docsPathInput.value = currentPath;
                closeDocsBrowser(document);
            });
        }

        if (docsBrowserCloseBtn && docsBrowserCloseBtn.dataset.boundSettings !== '1') {
            docsBrowserCloseBtn.dataset.boundSettings = '1';
            docsBrowserCloseBtn.addEventListener('click', function () {
                closeDocsBrowser(document);
            });
        }

        if (docsBrowserBackdrop && docsBrowserBackdrop.dataset.boundSettings !== '1') {
            docsBrowserBackdrop.dataset.boundSettings = '1';
            docsBrowserBackdrop.addEventListener('click', function () {
                closeDocsBrowser(document);
            });
        }

        if (embeddingModelSelect && embeddingModelSelect.dataset.boundSettings !== '1') {
            embeddingModelSelect.dataset.boundSettings = '1';
            embeddingModelSelect.addEventListener('change', function () {
                syncEmbeddingModelInputVisibility(document);
            });
        }

        if (embeddingModelCustomInput && embeddingModelCustomInput.dataset.boundSettings !== '1') {
            embeddingModelCustomInput.dataset.boundSettings = '1';
            embeddingModelCustomInput.addEventListener('input', function () {
                // Keep current input visible and user-controlled; validation happens on save.
            });
        }

        if (embeddingModelPrepareBtn && embeddingModelPrepareBtn.dataset.boundSettings !== '1') {
            embeddingModelPrepareBtn.dataset.boundSettings = '1';
            embeddingModelPrepareBtn.addEventListener('click', function () {
                startEmbeddingModelPullRequest(resolveEmbeddingModelSetting(document), document);
            });
        }

        if (customRoleImageSelect && customRoleImageSelect.dataset.boundSettings !== '1') {
            customRoleImageSelect.dataset.boundSettings = '1';
            customRoleImageSelect.addEventListener('change', function () {
                syncCustomRoleImagePreview(document);
            });
        }

        if (customRoleDefaultModelSelect && customRoleDefaultModelSelect.dataset.boundSettings !== '1') {
            customRoleDefaultModelSelect.dataset.boundSettings = '1';
            customRoleDefaultModelSelect.addEventListener('focus', function () {
                refreshCustomRoleDefaultModelSelect(document);
            });
        }

        if (customRoleDefaultStyleSelect && customRoleDefaultStyleSelect.dataset.boundSettings !== '1') {
            customRoleDefaultStyleSelect.dataset.boundSettings = '1';
            customRoleDefaultStyleSelect.addEventListener('change', function () {
                markResponseStale();
            });
        }

        if (customRolesExportBtn && customRolesExportBtn.dataset.boundSettings !== '1') {
            customRolesExportBtn.dataset.boundSettings = '1';
            customRolesExportBtn.addEventListener('click', async function () {
                try {
                    await exportServerCustomRoles(document);
                } catch (error) {
                    if (typeof showAlert === 'function') {
                        showAlert(error instanceof Error ? error.message : String(error), 'error', 4500);
                    }
                }
            });
        }

        if (customRolesImportBtn && customRolesImportBtn.dataset.boundSettings !== '1') {
            customRolesImportBtn.dataset.boundSettings = '1';
            customRolesImportBtn.addEventListener('click', function () {
                if (customRolesImportInput) {
                    customRolesImportInput.click();
                }
            });
        }

        if (customRolesImportInput && customRolesImportInput.dataset.boundSettings !== '1') {
            customRolesImportInput.dataset.boundSettings = '1';
            customRolesImportInput.addEventListener('change', async function () {
                const file = customRolesImportInput.files && customRolesImportInput.files[0]
                    ? customRolesImportInput.files[0]
                    : null;
                if (!file) {
                    return;
                }
                try {
                    await importServerCustomRoles(file, document);
                    if (typeof showAlert === 'function') {
                        showAlert(getSettingsText('settings_custom_roles_import_success', document, 'Custom roles imported.'), 'info', 3000);
                    }
                    markResponseStale();
                } catch (error) {
                    if (typeof showAlert === 'function') {
                        showAlert(error instanceof Error ? error.message : String(error), 'error', 4500);
                    }
                } finally {
                    customRolesImportInput.value = '';
                }
            });
        }

        if (customRolesResetBtn && customRolesResetBtn.dataset.boundSettings !== '1') {
            customRolesResetBtn.dataset.boundSettings = '1';
            customRolesResetBtn.addEventListener('click', async function () {
                const message = getSettingsText('settings_custom_roles_reset_confirm', document, 'Reset all shared custom roles?');
                if (window.confirm && !window.confirm(message)) {
                    return;
                }
                try {
                    await resetServerCustomRoles(document);
                    if (typeof showAlert === 'function') {
                        showAlert(getSettingsText('settings_custom_roles_reset_done', document, 'Shared custom roles reset.'), 'info', 3000);
                    }
                    markResponseStale();
                } catch (error) {
                    if (typeof showAlert === 'function') {
                        showAlert(error instanceof Error ? error.message : String(error), 'error', 4500);
                    }
                }
            });
        }

        if (customRoleSaveBtn && customRoleSaveBtn.dataset.boundSettings !== '1') {
            customRoleSaveBtn.dataset.boundSettings = '1';
            customRoleSaveBtn.addEventListener('click', function () {
                upsertCustomRoleFromEditor(document);
            });
        }

        if (customRoleClearBtn && customRoleClearBtn.dataset.boundSettings !== '1') {
            customRoleClearBtn.dataset.boundSettings = '1';
            customRoleClearBtn.addEventListener('click', function () {
                clearCustomRoleEditor(document);
            });
        }

        ROLE_KEYS.forEach(function (role) {
            const roleImageSelect = getRoleImageSelect(role, root);
            if (!roleImageSelect || roleImageSelect.dataset.boundPreview === '1') {
                return;
            }
            roleImageSelect.dataset.boundPreview = '1';
            roleImageSelect.addEventListener('change', function () {
                syncRoleImagePreview(role, document);
            });
        });

        if (saveBtn && saveBtn.dataset.boundSettings !== '1') {
            saveBtn.dataset.boundSettings = '1';
            saveBtn.addEventListener('click', async function () {
                const settings = collectSettingsFromModal(document);
                const draftCustomRoles = getDraftCustomRoles(document);
                const targetDocsPath = docsPathInput ? String(docsPathInput.value || '').trim() : '';
                const currentDocsPath = docsPathInput
                    ? String(docsPathInput.dataset.currentValue || docsPathInput.getAttribute('data-default-path') || '').trim()
                    : '';

                try {
                    settings.customRoles = await saveServerCustomRoles(draftCustomRoles, document);
                } catch (error) {
                    if (typeof showAlert === 'function') {
                        showAlert(error instanceof Error ? error.message : String(error), 'error', 4500);
                    }
                    return;
                }

                settings = syncServerCustomRolesToSettings(settings.customRoles, document, settings);

                const targetEmbeddingModel = resolveEmbeddingModelSetting(document);
                const currentEmbeddingModel = getCurrentEmbeddingModel(document);
                const runtimeConfig = {};

                if (embeddingModelSelect && String(embeddingModelSelect.value || '').trim() === 'custom' && !targetEmbeddingModel) {
                    if (typeof showAlert === 'function') {
                        showAlert(
                            getSettingsText('settings_embedding_model_invalid', document, 'Enter an embedding model.'),
                            'error',
                            4500
                        );
                    }
                    if (embeddingModelCustomInput) {
                        embeddingModelCustomInput.focus();
                    }
                    return;
                }

                if (docsPathInput && targetDocsPath && targetDocsPath !== currentDocsPath) {
                    runtimeConfig.docsPath = targetDocsPath;
                }
                if (targetEmbeddingModel && targetEmbeddingModel !== currentEmbeddingModel) {
                    runtimeConfig.embeddingModel = targetEmbeddingModel;
                }

                if (Object.keys(runtimeConfig).length) {
                    try {
                        await updateRuntimeConfigRequest(runtimeConfig, document);
                    } catch (error) {
                        if (typeof showAlert === 'function') {
                            const message = error instanceof Error ? error.message : getDocsPathUpdateFailedMessage();
                            showAlert(message, 'error', 4500);
                        }
                        if (runtimeConfig.embeddingModel && embeddingModelSelect) {
                            embeddingModelSelect.focus();
                        } else if (docsPathInput) {
                            docsPathInput.focus();
                        }
                        return;
                    }
                }

                markResponseStale();
                closeDocsBrowser(document);
                closeSettingsModal();
                refreshHistoryPanel();
            });
        }

        if (refreshModelsBtn && refreshModelsBtn.dataset.boundSettings !== '1') {
            refreshModelsBtn.dataset.boundSettings = '1';
            refreshModelsBtn.addEventListener('click', function () {
                loadModelManager(document);
            });
        }

        if (manualModelPullBtn && manualModelPullBtn.dataset.boundSettings !== '1') {
            manualModelPullBtn.dataset.boundSettings = '1';
            manualModelPullBtn.addEventListener('click', async function () {
                const modelName = manualModelInput ? manualModelInput.value : '';
                if (!normalizePreferredModel(modelName)) {
                    if (typeof showAlert === 'function') {
                        showAlert(getModelText('models_invalid_name', document, 'Enter a valid model name.'), 'error', 4000);
                    }
                    return;
                }
                const started = await startModelPullRequest(modelName, document);
                if (started && manualModelInput) {
                    manualModelInput.value = '';
                }
            });
        }

        if (resetBtn && resetBtn.dataset.boundSettings !== '1') {
            resetBtn.dataset.boundSettings = '1';
            resetBtn.addEventListener('click', function () {
                applySettingsToUi(buildResetSettings(document), document);
                if (docsPathInput) {
                    docsPathInput.value = docsPathInput.getAttribute('data-default-path') || docsPathInput.value;
                }
                closeDocsBrowser(document);
            });
        }

        if (modal && modal.dataset.boundSettings !== '1') {
            modal.dataset.boundSettings = '1';
            if (!window.__localRagSettingsEscapeBound) {
                window.__localRagSettingsEscapeBound = true;
                document.addEventListener('keydown', function (evt) {
                    if (evt.key === 'Escape') {
                        const currentModal = document.getElementById('settings-modal');
                        if (currentModal && !currentModal.hidden) {
                            closeDocsBrowser(document);
                            closeSettingsModal();
                        }
                    }
                });
            }
        }

        settingsTabs.forEach(function (button) {
            if (button.dataset.boundSettingsTab === '1') {
                return;
            }
            button.dataset.boundSettingsTab = '1';
            button.addEventListener('click', function () {
                activateSettingsTab(button.getAttribute('data-settings-tab') || 'general', document);
            });
        });

        if (!window.__localRagModelManagerActionsBound) {
            window.__localRagModelManagerActionsBound = true;
            document.addEventListener('click', function (evt) {
                const docsTrigger = evt.target && evt.target.closest ? evt.target.closest('[data-docs-browser-path]') : null;
                if (docsTrigger) {
                    const nextPath = String(docsTrigger.getAttribute('data-docs-browser-path') || '').trim();
                    if (nextPath) {
                        loadDocsBrowser(nextPath, document);
                    }
                    return;
                }
                const customRoleTrigger = evt.target && evt.target.closest ? evt.target.closest('[data-custom-role-action]') : null;
                if (customRoleTrigger) {
                    const action = String(customRoleTrigger.getAttribute('data-custom-role-action') || '');
                    const roleId = String(customRoleTrigger.getAttribute('data-custom-role-id') || '');
                    if (action === 'edit') {
                        const role = getDraftCustomRoles(document).find(function (entry) {
                            return entry.id === roleId;
                        }) || null;
                        populateCustomRoleEditor(role, document);
                    }
                    if (action === 'delete') {
                        deleteCustomRole(roleId, document);
                    }
                    return;
                }
                const embeddingTrigger = evt.target && evt.target.closest ? evt.target.closest('[data-embedding-model-action]') : null;
                if (embeddingTrigger) {
                    const action = String(embeddingTrigger.getAttribute('data-embedding-model-action') || '');
                    const modelName = String(embeddingTrigger.getAttribute('data-embedding-model-name') || '');
                    if (action === 'prepare') {
                        startEmbeddingModelPullRequest(modelName, document);
                    }
                    if (action === 'use') {
                        selectEmbeddingModel(modelName, document);
                    }
                    return;
                }
                const trigger = evt.target && evt.target.closest ? evt.target.closest('[data-model-action]') : null;
                if (!trigger) {
                    return;
                }
                const action = String(trigger.getAttribute('data-model-action') || '');
                const modelName = String(trigger.getAttribute('data-model-name') || '');
                if (action === 'pull-model') {
                    startModelPullRequest(modelName, document);
                }
                if (action === 'delete-model') {
                    deleteModelRequest(modelName, document);
                }
                if (action === 'set-default-model') {
                    applyPreferredModelSetting(modelName, document);
                    if (typeof showAlert === 'function') {
                        showAlert(getModelText('models_default_badge', document, 'Default') + ': ' + modelName, 'info', 2500);
                    }
                }
            });
        }
    }

    function syncTopk(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const slider = root.querySelector('#topk-slider');
        const hidden = root.querySelector('#topk-hidden') || document.getElementById('topk-hidden');
        const value = root.querySelector('#topk-value') || document.getElementById('topk-value');
        if (slider && hidden) {
            hidden.value = slider.value;
        }
        if (slider && value) {
            value.textContent = slider.value;
        }
    }

    function syncModel(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const modelEl = root.querySelector('#model') || document.getElementById('model');
        const hidden = root.querySelector('#model-hidden') || document.getElementById('model-hidden');
        if (modelEl && hidden) {
            hidden.value = modelEl.value || '';
        }
    }

    function syncRole(scope, settings) {
        const root = scope instanceof HTMLElement ? scope : document;
        const hidden = root.querySelector('#role-hidden') || document.getElementById('role-hidden');
        const roleLabelHidden = getRoleLabelHidden(root);
        const selected = root.querySelector('input[name="role-selector"]:checked')
            || document.querySelector('input[name="role-selector"]:checked');
        if (hidden && selected) {
            const selectedRole = normalizeRoleId(selected.value);
            hidden.value = selectedRole;
            if (roleLabelHidden) {
                const definition = getRoleDefinitionById(selectedRole, settings || getSettings(), root);
                roleLabelHidden.value = definition ? definition.name || selectedRole : selectedRole;
            }
        }
        syncCustomRolePrompt(root, settings || getSettings());
    }

    function updateRoleSelection(scope) {
        const root = scope instanceof HTMLElement ? scope : document;
        const cards = root.querySelectorAll('.role-card');
        if (!cards.length) {
            return;
        }
        cards.forEach(function (card) {
            card.classList.remove('is-selected');
            const radio = card.querySelector('input[name="role-selector"]');
            if (radio && radio.checked) {
                card.classList.add('is-selected');
            }
        });
    }

    function updateAskState() {
        const askBtn = document.getElementById('ask-btn');
        if (!askBtn) {
            return;
        }
        const modelEl = document.getElementById('model');
        const question = document.getElementById('question');
        const hasModel = !!(modelEl && modelEl.value && !modelEl.disabled);
        const hasQuestion = !!(question && question.value.trim().length > 0);
        askBtn.disabled = askRequestPending || !(hasModel && hasQuestion);
    }

    function showAskProgress() {
        askRequestPending = true;
        const progress = document.getElementById('ask-progress');
        if (progress) {
            progress.classList.add('is-active');
        }
        updateAskState();
    }

    function hideAskProgress() {
        askRequestPending = false;
        const progress = document.getElementById('ask-progress');
        if (progress) {
            progress.classList.remove('is-active');
        }
        updateAskState();
    }

    function resizeAnswerTextarea(answer) {
        if (!(answer instanceof HTMLTextAreaElement)) {
            return;
        }
        const minHeight = 220;
        const maxHeight = 700;
        answer.style.height = 'auto';
        const nextHeight = Math.max(minHeight, Math.min(maxHeight, answer.scrollHeight || minHeight));
        answer.style.height = String(nextHeight) + 'px';
        answer.style.overflowY = (answer.scrollHeight || nextHeight) > maxHeight ? 'auto' : 'hidden';
    }

    function setResponsePlaceholder(message, options) {
        const settings = options && typeof options === 'object' ? options : {};
        const responsePanel = document.getElementById('ask-response');
        if (responsePanel) {
            responsePanel.classList.toggle('is-stale', !!settings.isStale);
        }

        const answer = document.getElementById('answer');
        if (answer) {
            answer.value = message;
            resizeAnswerTextarea(answer);
        }

        const contextPanel = document.getElementById('context-panel');
        const contextContent = document.getElementById('context-content');
        if (contextPanel) {
            contextPanel.open = false;
        }
        if (contextContent) {
            contextContent.innerHTML = '<p class="muted">' + escapeHtml(message) + '</p>';
        }

        document.querySelectorAll('#ask-response .debug-card').forEach(function (node) {
            node.remove();
        });
    }

    function beginAskRequest() {
        setResponsePlaceholder(getLoadingMessage(), { isStale: false });
    }

    function markResponseStale() {
        if (askRequestPending) {
            return;
        }
        const answer = document.getElementById('answer');
        if (!answer) {
            return;
        }
        const currentValue = String(answer.value || '').trim();
        if (!currentValue) {
            return;
        }
        if (currentValue === getLoadingMessage() || currentValue === getStaleMessage()) {
            return;
        }
        setResponsePlaceholder(getStaleMessage(), { isStale: true });
    }

    function applyDirection(scope) {
        let container = null;
        if (scope instanceof HTMLElement) {
            container = scope.id === 'app' ? scope : scope.closest('#app');
        }
        if (!container) {
            container = document.getElementById('app');
        }
        if (!container) {
            return;
        }
        const dir = container.getAttribute('data-dir') || document.body.getAttribute('data-dir') || 'ltr';
        const lang = container.getAttribute('data-lang') || document.body.getAttribute('data-current-lang') || 'en';
        document.documentElement.setAttribute('dir', dir);
        document.documentElement.setAttribute('lang', lang);
        document.body.setAttribute('data-current-lang', lang);
        document.body.setAttribute('data-dir', dir);
        if (dir === 'rtl') {
            document.body.classList.add('rtl');
        } else {
            document.body.classList.remove('rtl');
        }
    }

    function initUi(scope) {
        applyDirection(scope);
        refreshSettingsDefaultsFromDom();
        syncTopk(scope);
        syncModel(scope);
        const settings = loadSettings();
        window.LocalRagSettings = settings;
        applySettingsToUi(settings, scope);
        bindSettingsModal(scope);
        resizeAnswerTextarea(document.getElementById('answer'));
        updateAskState();
        hideAskProgress();
        syncStatusPolling();
    }

    document.addEventListener('DOMContentLoaded', function () {
        initUi(document);
        if (window.htmx) {
            const statusCard = document.getElementById('status-card');
            if (statusCard) {
                window.htmx.trigger(statusCard, 'refreshStatus');
            }
            const modelEl = document.getElementById('model');
            if (modelEl) {
                window.htmx.trigger(modelEl, 'refreshModels');
            }
            refreshHistoryPanel();
        }
    });

    document.addEventListener('input', function (evt) {
        if (evt.target && evt.target.id === 'topk-slider') {
            syncTopk(document);
            markResponseStale();
        }
        if (evt.target && evt.target.id === 'question') {
            updateAskState();
            markResponseStale();
        }
    });

    document.addEventListener('change', function (evt) {
        if (evt.target && evt.target.id === 'model') {
            syncModel(document);
            updateAskState();
            markResponseStale();
        }
        if (evt.target && evt.target.name === 'role-selector') {
            syncRole(document, getSettings());
            updateRoleSelection(document);
            markResponseStale();
        }
    });

    if (window.htmx) {
        window.htmx.onLoad(function (elt) {
            initUi(elt);
            if (elt && elt.id === 'app') {
                const statusCard = document.getElementById('status-card');
                if (statusCard) {
                    window.htmx.trigger(statusCard, 'refreshStatus');
                }
                const modelEl = document.getElementById('model');
                if (modelEl) {
                    window.htmx.trigger(modelEl, 'refreshModels');
                }
                refreshHistoryPanel();
            }
        });
        document.body.addEventListener('htmx:afterSwap', function (evt) {
            if (evt.detail && evt.detail.elt && evt.detail.elt.id === 'model') {
                refreshCustomRoleDefaultModelSelect(document);
                syncRole(document, getSettings());
                updateAskState();
            }
            if (evt.detail && evt.detail.elt && evt.detail.elt.id === 'status-card') {
                syncStatusPolling();
            }
        });
        document.body.addEventListener('htmx:beforeRequest', function (evt) {
            const source = evt && evt.detail ? evt.detail.elt : null;
            if (source && source.id === 'ask-form') {
                beginAskRequest();
                showAskProgress();
            }
        });
        document.body.addEventListener('htmx:afterRequest', function (evt) {
            const source = evt && evt.detail ? evt.detail.elt : null;
            if (source && source.id === 'ask-form') {
                hideAskProgress();
            }
        });
        document.body.addEventListener('htmx:afterSwap', function (evt) {
            const target = evt && evt.detail ? evt.detail.target : null;
            if (target && target.id === 'ask-response') {
                target.classList.remove('is-stale');
                resizeAnswerTextarea(document.getElementById('answer'));
                hideAskProgress();
                refreshHistoryPanel();
            }
        });
        document.body.addEventListener('htmx:afterSettle', function (evt) {
            if (evt.target && evt.target.id === 'ask-response') {
                updateAskState();
            }
        });
    } else {
        setTimeout(updateAskState, 10);
    }
})();

// alert.js: Simple alert/loader system for LocalRAG

(function () {
    const alertBlock = document.getElementById('alert-block');
    const loaderOverlay = document.getElementById('global-loader');

    function clearAlert() {
        if (alertBlock) {
            alertBlock.innerHTML = '';
        }
    }

    function showAlert(message, type = 'info', timeout = 3500) {
        if (!alertBlock) {
            return;
        }
        alertBlock.innerHTML = `<div class="alert alert-${type}" role="status">${message}</div>`;
        if (timeout > 0) {
            setTimeout(clearAlert, timeout);
        }
    }

    function showLoader() {
        if (!loaderOverlay) {
            return;
        }
        loaderOverlay.hidden = false;
        loaderOverlay.setAttribute('aria-hidden', 'false');
        requestAnimationFrame(function () {
            loaderOverlay.classList.add('is-active');
        });
    }

    function hideLoader() {
        if (!loaderOverlay) {
            return;
        }
        loaderOverlay.classList.remove('is-active');
        loaderOverlay.setAttribute('aria-hidden', 'true');
        setTimeout(function () {
            if (loaderOverlay && !loaderOverlay.classList.contains('is-active')) {
                loaderOverlay.hidden = true;
            }
        }, 220);
    }

    function hideAlert() {
        clearAlert();
        hideLoader();
    }

    window.showAlert = showAlert;
    window.hideAlert = hideAlert;
    window.showLoader = showLoader;
    window.hideLoader = hideLoader;

    // htmx global events for loader UX
    if (window.htmx) {
        document.body.addEventListener('htmx:beforeRequest', function (evt) {
            showLoader();
        });
        document.body.addEventListener('htmx:afterSwap', function () {
            hideLoader();
        });
        document.body.addEventListener('htmx:afterRequest', function () {
            hideLoader();
        });
        document.body.addEventListener('htmx:responseError', function (evt) {
            hideLoader();
            showAlert('Server error', 'error', 5000);
        });
    }
})();

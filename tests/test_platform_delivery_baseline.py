import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT_DIR / "deploy" / "platform-delivery" / "platform-delivery-baseline.json"
COOLIFY_ENV_PATH = ROOT_DIR / "deploy" / "coolify" / "localrag.env.example"


def load_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def read_env_names(path: Path) -> set[str]:
    names: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, _value = line.partition("=")
        names.add(name)
    return names


def test_platform_delivery_baseline_confirms_required_environments():
    baseline = load_baseline()

    environments = baseline["environments"]
    env_names = {item["name"] for item in environments}
    assert env_names == {"dev", "staging", "prod"}
    assert baseline["definition_of_done"]["environments_confirmed"] == [
        "dev",
        "staging",
        "prod",
    ]

    for item in environments:
        assert item["app_env"] == item["name"]
        assert item["url_variable"].startswith("LOCALRAG_")
        assert "/api/health" in item["readiness_endpoints"]
        assert "/api/meta" in item["readiness_endpoints"]


def test_gitlab_secret_map_contains_delivery_and_monitoring_variables():
    baseline = load_baseline()
    secret_map = baseline["gitlab"]["secret_map"]
    names = {item["name"] for item in secret_map}

    required_names = {
        "LOCALRAG_EVAL_BASE_URL",
        "GITHUB_PUSH_TOKEN",
        "KIWI_USERNAME",
        "KIWI_PASSWORD",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_ZONE_ID",
        "COOLIFY_DEPLOY_WEBHOOK_URL",
        "COOLIFY_API_TOKEN",
        "GRAYLOG_HTTP_INPUT_URL",
        "GRAYLOG_HTTP_INPUT_TOKEN",
        "UPTIME_KUMA_PUSH_TOKEN",
        "MAYALERTS_SOURCE_SECRET",
        "MAYALERTS_GITLAB_TOKEN",
    }
    assert required_names <= names

    for item in secret_map:
        assert item["owner"]
        assert item["scope_envs"]
        assert item["required_for"]
        if item["kind"] == "secret":
            assert item["masked"] is True
        if {"staging", "prod"} & set(item["scope_envs"]):
            assert item["protected"] is True


def test_platform_delivery_baseline_covers_external_setup_systems():
    baseline = load_baseline()

    kiwi = baseline["kiwi"]
    assert kiwi["product"]["name"] == "LocalRAG"
    assert kiwi["version"]["name"] == baseline["project"]["release_version"]
    assert kiwi["build"]["name_template"].startswith("localrag-0.9.0-")
    assert kiwi["mapping_file"] == "tests/kiwi_sync_mapping.json"

    cloudflare = baseline["cloudflare"]
    assert cloudflare["tls"]["mode"] == "Full (strict)"
    assert {record["environment"] for record in cloudflare["dns_records"]} == {
        "dev",
        "staging",
        "prod",
    }

    coolify = baseline["coolify"]
    assert coolify["application"]["type"] == "docker-compose"
    assert coolify["application"]["compose_file"] == "docker-compose.yml"
    assert coolify["application"]["container_port"] == 7860
    assert "SERVICE_NAME" in coolify["environment_variables"]
    assert "APP_ENV" in coolify["environment_variables"]
    assert "MAYALERTS_SOURCE_SECRET" in coolify["environment_variables"]


def test_monitoring_baseline_includes_alert_sources_and_gitlab_routing():
    baseline = load_baseline()
    monitoring = baseline["monitoring"]

    graylog_events = set(monitoring["graylog"]["event_definitions"])
    assert "localrag_health_down" in graylog_events
    assert "localrag_release_drift" in graylog_events
    assert "localrag_observability_contract_violation" in graylog_events

    kuma_checks = monitoring["uptime_kuma"]["checks"]
    assert {check["environment"] for check in kuma_checks} == {
        "dev",
        "staging",
        "prod",
    }
    assert all(
        check["url_template"].endswith(("/api/health", "/api/meta", "/"))
        for check in kuma_checks
    )

    mayalerts = monitoring["mayalerts"]
    assert mayalerts["source"] == "localrag-platform-delivery"
    assert mayalerts["source_secret_variable"] == "MAYALERTS_SOURCE_SECRET"
    assert mayalerts["gitlab_routing"]["project_path"] == "myprojects/localrag"
    assert mayalerts["gitlab_routing"]["prod_confidential"] is True


def test_coolify_env_template_matches_declared_environment_set():
    baseline = load_baseline()
    declared = set(baseline["coolify"]["environment_variables"])
    env_names = read_env_names(COOLIFY_ENV_PATH)

    assert declared <= env_names
    assert "SERVICE_NAME" in env_names
    assert "APP_RELEASE" in env_names
    assert "GRAYLOG_HTTP_INPUT_TOKEN" in env_names

from fastapi.testclient import TestClient
import pytest

import main


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_model_state():
    main.reset_model_pull_state()
    yield
    main.reset_model_pull_state()


def test_models_data_returns_installed_and_recommended(monkeypatch):
    monkeypatch.setattr(
        main,
        'fetch_ollama_model_inventory',
        lambda: [
            {
                'name': 'phi3:mini',
                'size': 123456789,
                'modified_at': '2026-03-08T09:00:00Z',
                'digest': 'sha256:abc',
                'details': {
                    'family': 'phi3',
                    'families': ['phi3'],
                    'parameter_size': '3.8B',
                    'quantization_level': 'Q4_K_M',
                    'format': 'gguf',
                },
            }
        ],
    )

    resp = client.get('/api/models/data')

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True
    assert payload['installed'][0]['name'] == 'phi3:mini'
    assert any(item['name'] == 'qwen3:8b' for item in payload['recommended'])
    assert payload['pull']['status'] == 'idle'


def test_models_pull_endpoint_starts_job(monkeypatch):
    monkeypatch.setattr(
        main,
        'start_model_pull',
        lambda model_name: {'ok': True, 'message': 'pull_started', 'model': model_name},
    )
    monkeypatch.setattr(
        main,
        'build_model_manager_payload',
        lambda t_local: {
            'ok': True,
            'installed': [],
            'default_model': '',
            'recommended': [],
            'pull': {'active': True, 'model': 'qwen3:8b', 'status': 'starting', 'label': 'Preparing model download...'},
        },
    )

    resp = client.post('/api/models/pull', json={'model': 'qwen3:8b'})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True
    assert 'qwen3:8b' in payload['message']
    assert payload['pull']['active'] is True


def test_models_delete_endpoint_returns_success(monkeypatch):
    monkeypatch.setattr(
        main,
        'delete_ollama_model',
        lambda model_name: {'ok': True, 'message': 'model_deleted', 'model': model_name},
    )
    monkeypatch.setattr(
        main,
        'build_model_manager_payload',
        lambda t_local: {
            'ok': True,
            'installed': [],
            'default_model': '',
            'recommended': [],
            'pull': {'active': False, 'model': '', 'status': 'idle', 'label': 'No active download.'},
        },
    )

    resp = client.post('/api/models/delete', json={'model': 'phi3:mini'})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True
    assert 'phi3:mini' in payload['message']


def test_models_pull_endpoint_rejects_invalid_name(monkeypatch):
    monkeypatch.setattr(
        main,
        'build_model_manager_payload',
        lambda t_local: {
            'ok': True,
            'installed': [],
            'default_model': '',
            'recommended': [],
            'pull': {'active': False, 'model': '', 'status': 'idle', 'label': 'No active download.'},
        },
    )

    resp = client.post('/api/models/pull', json={'model': 'bad model name'})

    assert resp.status_code == 400
    payload = resp.json()
    assert payload['ok'] is False
    assert 'valid model name' in payload['message']

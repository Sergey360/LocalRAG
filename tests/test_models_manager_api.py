from fastapi.testclient import TestClient
import pytest

import main


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_model_state():
    main.reset_model_pull_state()
    main.reset_embedding_model_pull_state()
    yield
    main.reset_model_pull_state()
    main.reset_embedding_model_pull_state()


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


def test_models_pull_endpoint_translates_not_found_error(monkeypatch):
    monkeypatch.setattr(
        main,
        'start_model_pull',
        lambda model_name: {
            'ok': False,
            'message': 'pull model manifest: file does not exist',
            'model': model_name,
        },
    )
    monkeypatch.setattr(
        main,
        'build_model_manager_payload',
        lambda t_local: {
            'ok': True,
            'installed': [],
            'default_model': '',
            'recommended': [],
            'pull': {'active': False, 'model': 'google/translategemma-12b-it', 'status': 'error', 'label': 'Model download failed.'},
        },
    )

    resp = client.post('/api/models/pull', json={'model': 'google/translategemma-12b-it'})

    assert resp.status_code == 400
    payload = resp.json()
    assert payload['ok'] is False
    assert 'not found in the Ollama library' in payload['message']


def test_models_pull_status_translates_not_found_error():
    main.reset_model_pull_state()
    main.update_model_pull_state(
        active=False,
        model='google/translategemma-12b-it',
        status='error',
        error='pull model manifest: file does not exist',
    )

    resp = client.get('/api/models/pull_status')

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['pull']['status'] == 'error'
    assert 'not found in the Ollama library' in payload['pull']['label']


def test_embedding_models_data_returns_available_and_recommended(monkeypatch):
    monkeypatch.setattr(
        main,
        'list_available_embedding_models',
        lambda: [{'name': 'BAAI/bge-m3', 'source': 'cache', 'path': ''}],
    )
    monkeypatch.setattr(
        main,
        'get_recommended_embedding_models',
        lambda t_local: [
            {'name': 'intfloat/multilingual-e5-large', 'summary': 'Baseline', 'available': True},
            {'name': 'Alibaba-NLP/gte-multilingual-base', 'summary': 'Alt', 'available': False},
        ],
    )

    resp = client.get('/api/embedding-models/data')

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True
    assert payload['available'][0]['name'] == 'BAAI/bge-m3'
    assert payload['recommended'][0]['name'] == 'intfloat/multilingual-e5-large'
    assert payload['pull']['status'] == 'idle'


def test_embedding_models_pull_endpoint_starts_job(monkeypatch):
    monkeypatch.setattr(
        main,
        'start_embedding_model_pull',
        lambda model_name: {'ok': True, 'message': 'prepare_started', 'model': model_name},
    )
    monkeypatch.setattr(
        main,
        'build_embedding_model_manager_payload',
        lambda t_local: {
            'ok': True,
            'available': [],
            'current_model': 'intfloat/multilingual-e5-large',
            'default_model': 'intfloat/multilingual-e5-large',
            'recommended': [],
            'runtime': {'device': 'cuda'},
            'pull': {'active': True, 'model': 'Alibaba-NLP/gte-multilingual-base', 'status': 'starting', 'label': 'Preparing embedding model...'},
        },
    )

    resp = client.post('/api/embedding-models/pull', json={'embedding_model': 'Alibaba-NLP/gte-multilingual-base'})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload['ok'] is True
    assert 'Alibaba-NLP/gte-multilingual-base' in payload['message']
    assert payload['pull']['active'] is True


def test_embedding_models_pull_endpoint_rejects_invalid_name(monkeypatch):
    monkeypatch.setattr(
        main,
        'build_embedding_model_manager_payload',
        lambda t_local: {
            'ok': True,
            'available': [],
            'current_model': 'intfloat/multilingual-e5-large',
            'default_model': 'intfloat/multilingual-e5-large',
            'recommended': [],
            'runtime': {'device': 'cpu'},
            'pull': {'active': False, 'model': '', 'status': 'idle', 'label': 'No active embedding model preparation.'},
        },
    )

    resp = client.post('/api/embedding-models/pull', json={'embedding_model': '   '})

    assert resp.status_code == 400
    payload = resp.json()
    assert payload['ok'] is False


def test_ollama_pull_worker_marks_error_from_stream_event(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        def iter_lines(self, decode_unicode=True):
            yield '{"status":"pulling manifest"}'
            yield '{"error":"pull model manifest: file does not exist"}'

    monkeypatch.setattr(main.requests, 'post', lambda *args, **kwargs: FakeResponse())

    main.reset_model_pull_state()
    main._pull_model_worker('google/translategemma-12b-it')

    state = main.get_model_pull_state()
    assert state['status'] == 'error'
    assert 'file does not exist' in state['error']

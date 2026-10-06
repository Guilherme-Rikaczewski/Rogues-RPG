from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.services.auth_service import get_current_user_id
from tests.helpers import USER_ID, make_db


@pytest.fixture(autouse=True)
def block_external_services():
    """Garante que nenhum teste chame o Cloudinary ou o Gemini de verdade.

    Os testes devem mockar upload_image/delete_image/genai.Client no módulo
    que estão testando. Se algum esquecer, este fixture falha o teste
    (inclusive quando o código engole a exceção, como delete_image faz).
    """
    blocked = {
        "cloudinary.uploader.upload": MagicMock(),
        "cloudinary.uploader.destroy": MagicMock(),
        "google.genai.Client": MagicMock(),
    }

    patchers = [
        patch(target, mock) for target, mock in blocked.items()
    ]
    for patcher in patchers:
        patcher.start()

    yield

    for patcher in patchers:
        patcher.stop()

    called = [target for target, mock in blocked.items() if mock.called]
    assert not called, f"Teste chamou serviço externo real: {called}"


@pytest.fixture
def db():
    return make_db()


@pytest.fixture
def client(db):
    """TestClient com o banco mockado e sem usuário logado.

    Sem o `with TestClient(...)` o lifespan não roda, então a aplicação
    não tenta conectar no Postgres nem no Redis.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """TestClient autenticado como USER_ID."""
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID

    return client

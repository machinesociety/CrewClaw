import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import (
    get_runtime_binding_repository,
    get_session_repository,
    get_sqlalchemy_user_repository,
    get_user_service,
)
from app.main import create_app
from app.core.sessions import create_session
from app.core.settings import get_settings
from app.repositories.session_repository import InMemorySessionRepository
from app.repositories.user_repository import InMemoryUserRepository
from app.services.user_service import UserService


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture
def client(app):
    session_repo = InMemorySessionRepository()
    app.dependency_overrides[get_session_repository] = lambda: session_repo
    with TestClient(app) as c:
        c._session_repo = session_repo  # type: ignore[attr-defined]
        yield c
    app.dependency_overrides.clear()


class _InMemoryBindingRepo:
    def __init__(self) -> None:
        self._bindings: dict[str, "UserRuntimeBinding"] = {}

    def get_by_user_id(self, user_id: str):
        from app.domain.users import UserRuntimeBinding

        return self._bindings.get(user_id)

    def save(self, binding):
        self._bindings[binding.user_id] = binding


def _make_user_repo():
    return InMemoryUserRepository()


def _make_binding_repo():
    return _InMemoryBindingRepo()


def _make_user_service(user_repo, binding_repo):
    return UserService(
        user_repo=user_repo,
        binding_repo=binding_repo,
        default_image_ref="clawloops-runtime-wrapper:openclaw-1.0.0",
        default_retention_policy="preserve_workspace",
    )


@pytest.fixture
def client_with_inmemory(app):
    """Fixture that overrides user/binding repos and UserService with in-memory implementations."""
    user_repo = _make_user_repo()
    binding_repo = _make_binding_repo()
    service = _make_user_service(user_repo, binding_repo)
    session_repo = InMemorySessionRepository()

    app.dependency_overrides[get_sqlalchemy_user_repository] = lambda: user_repo
    app.dependency_overrides[get_runtime_binding_repository] = lambda: binding_repo
    app.dependency_overrides[get_user_service] = lambda: service
    app.dependency_overrides[get_session_repository] = lambda: session_repo

    with TestClient(app) as c:
        # attach repos for tests that want to seed data
        c._user_repo = user_repo  # type: ignore[attr-defined]
        c._binding_repo = binding_repo  # type: ignore[attr-defined]
        c._session_repo = session_repo  # type: ignore[attr-defined]
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def issue_session_cookie():
    """
    Helper that creates a server-side session and sets cookie on TestClient.
    Usage: issue_session_cookie(client, user_id)
    """

    settings = get_settings()

    def _issue(client: TestClient, *, user_id: str) -> str:
        sess = create_session(ttl_seconds=settings.session_ttl_seconds)
        repo: InMemorySessionRepository = client._session_repo  # type: ignore[attr-defined]
        repo.create(
            user_id=user_id,
            session_id_hash=sess.token_hash,
            issued_at=sess.issued_at,
            expires_at=sess.expires_at,
            created_by_ip=None,
            user_agent=None,
        )
        client.cookies.set(settings.session_cookie_name, sess.token)
        return sess.token

    return _issue



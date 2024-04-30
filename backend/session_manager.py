from typing import Generic
from fastapi import HTTPException, Request, Response
from uuid import UUID, uuid4

from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.backends.session_backend import SessionBackend, SessionModel


class InvalidSessionException(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail="Invalid session")


class BasicVerifier(SessionVerifier[UUID, SessionModel]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionModel],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionModel) -> bool:
        """If the session exists, it is valid"""
        return True


class SessionManager(Generic[SessionModel]):
    """Session manager."""

    def __init__(
        self, backend: SessionBackend = None, verifier: SessionVerifier = None
    ):
        self.backend = backend or InMemoryBackend[UUID, SessionModel]()
        self.verifier = verifier or BasicVerifier(
            identifier="general_verifier",
            auto_error=True,
            backend=self.backend,
            auth_http_exception=InvalidSessionException(),
        )
        cookie_params = CookieParameters()
        self.cookie = SessionCookie(
            cookie_name="session_id",
            identifier="general_verifier",
            auto_error=True,
            secret_key="DONOTUSE",
            cookie_params=cookie_params,
        )

    async def create_session(self, response: Response, data: SessionModel):
        """Create a new session and attach it to the response."""
        session = uuid4()
        await self.backend.create(session, data)
        self.cookie.attach_to_response(response, session)
        return session

    def get_session_id(self, request: Request) -> UUID:
        return self.cookie(request)

    async def delete_session(self, request: Request, response: Response):
        """Delete the current session."""
        session_id = self.cookie(request)
        await self.backend.delete(session_id)
        self.cookie.delete_from_response(response)

    async def __call__(self, request: Request) -> SessionModel:
        """Get the current session, if any"""
        self.cookie(request)
        return await self.verifier(request)

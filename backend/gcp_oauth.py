"""Google OAuth2 class."""

from typing import Any
from urllib.parse import urlparse, urlunparse
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import requests
import fnmatch
from jose import jwt
from jose.exceptions import JWTError

GOOGLE_URL_PUBLIC_KEYS = "https://www.googleapis.com/oauth2/v1/certs"
GOOGLE_URL_AUTH = "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={}&redirect_uri={}&scope=openid%20profile%20email&access_type=offline"
GOOGLE_URL_TOKEN = "https://accounts.google.com/o/oauth2/token"
GOOGLE_URL_USERINFO = "https://www.googleapis.com/oauth2/v1/userinfo"


class UserData(BaseModel):
    email: str
    name: str
    given_name: str
    family_name: str
    picture: str


class OAuth:
    """Google OAuth2 class."""

    def __init__(
        self,
        client_id,
        client_secret,
        redirect_uri: str = "/auth",
        included_paths: list[str] = None,
        excluded_paths: list[str] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.included_paths = included_paths or ["/*"]
        self.excluded_paths = excluded_paths or [
            "/login",
            "/auth",
            "/favicon.ico",
        ]
        self._google_public_keys = self._get_google_public_keys()

    def _get_google_public_keys(self):
        r = requests.get(GOOGLE_URL_PUBLIC_KEYS)
        keys = r.json()
        return keys

    def redirect_login(self, request: Request = None):
        """Redirect to Google login page."""
        self.set_redirect_uri(request)
        return RedirectResponse(
            url=GOOGLE_URL_AUTH.format(self.client_id, self.redirect_uri)
        )

    def set_redirect_uri(self, request: Request):
        """Set redirect_uri to the current request path."""
        parsed_url = urlparse(self.redirect_uri)
        if not parsed_url.scheme or not parsed_url.netloc:
            scheme = request.url.scheme
            host = request.url.hostname
            port = request.url.port
            if (
                not port
                or (scheme == "http" and port == 80)
                or (scheme == "https" and port == 443)
            ):
                netloc = host
            else:
                netloc = f"{host}:{port}"
            self.redirect_uri = urlunparse(
                (
                    scheme,
                    netloc,
                    parsed_url.path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment,
                )
            )

    async def auth(self, code: str) -> UserData:
        """Authenticate user with Google OAuth2 and return user info."""
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        response = requests.post(GOOGLE_URL_TOKEN, data=data)
        access_token = response.json().get("access_token")
        user_info = requests.get(
            GOOGLE_URL_USERINFO,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return UserData.model_validate(user_info.json())

    async def verify_token_middleware(self, request: Request, call_next) -> Response:
        """Verify token middleware."""
        if self.requre_auth(request):
            token = request.headers.get("Authorization")
            if token:
                token = token.split(" ")[1]
                try:
                    self.verify_jwt(token)
                except Exception:
                    return Response(content="Invalid token signature", status_code=401)
            else:
                return Response(content="Unauthorized", status_code=401)
        response = await call_next(request)
        return response

    def verify_token(self, request: Request) -> dict[str, Any] | None:
        """Verify token."""
        token = request.headers.get("Authorization")
        if token:
            token = token.split(" ")[1]
            print(token)
            return self.verify_jwt(token)
        return None

    def requre_auth(self, request: Request) -> bool:
        """Check if the request path requires authentication."""
        return any(
            fnmatch.fnmatch(request.url.path, pattern)
            for pattern in self.included_paths
        ) and not any(
            fnmatch.fnmatch(request.url.path, pattern)
            for pattern in self.excluded_paths
        )

    def verify_jwt(self, token) -> dict[str, Any] | None:
        """Verify Google JWT token and return decoded token."""
        try:
            decoded_token = jwt.decode(
                token,
                self._google_public_keys,
                algorithms=["RS256"],
                audience=self.client_id,
            )
            return decoded_token
        except JWTError:
            return None

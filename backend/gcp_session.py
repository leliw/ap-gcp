from typing import Type, TypeVar
from fastapi import HTTPException, Request, Response
from pydantic import BaseModel
from gcp_oauth import OAuth, UserData
from session_manager import (
    InvalidSessionException,
    SessionManager as BaseSessionManager,
)


class SessionData(BaseModel):
    user: UserData

SessionModel = TypeVar("SessionModel", bound=SessionData)

class SessionManager(BaseSessionManager[SessionModel]):
    """Session manager for GCP."""

    def __init__(self, o_auth: OAuth, session_class: Type[SessionModel] = SessionData):
        super().__init__()
        self.o_auth = o_auth
        self.session_class = session_class

    async def session_reader(
        self, request: Request, response: Response
    ) -> SessionModel:
        try:
            data = await self.__call__(request)
            return data
        except InvalidSessionException:
            pass
        except HTTPException as e:
            if e.status_code != 403 or e.detail != "No session provided":
                raise e
        user_data = self.o_auth.verify_token(request)
        if not user_data:
            raise HTTPException(status_code=401, detail="Unauthorized")
        data = self.create_session_for_user(user_data)
        await self.create_session(response, data)
        return data
    
    def create_session_for_user(self, user_data: UserData) -> SessionModel:
        return self.session_class(user=user_data)
    
    

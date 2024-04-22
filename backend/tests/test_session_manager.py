import unittest
from fastapi import Depends, FastAPI, Request, Response
from fastapi.testclient import TestClient
from pydantic import BaseModel
from session_manager import SessionManager


class SessionData(BaseModel):
    username: str


class TestSessionManager(unittest.TestCase):
    """Test GCP session manager."""
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = FastAPI()
        session_manager = SessionManager[SessionData]()

        @cls.app.post("/create_session/{name}")
        async def create_session(name: str, response: Response):
            await session_manager.create_session(response, SessionData(username=name))
            return f"created session for {name}"

        @cls.app.get("/whoami")
        async def whoami(session_data: SessionData = Depends(session_manager)):
            return session_data

        @cls.app.post("/delete_session")
        async def del_session(request: Request, response: Response):
            await session_manager.delete_session(request, response)
            return "session deleted"

        return super().setUpClass()

    def setUp(self):
        self.client = TestClient(self.app)

    def test_gcp_session(self):
        response = self.client.post("/create_session/test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual("created session for test", response.text.strip('"'))
        self.assertIn("session_id", response.cookies)

        response = self.client.get(
            "/whoami", cookies={"session_id": response.cookies.get("session_id")}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"username": "test"})

        response = self.client.post(
            "/delete_session",
            cookies={"session_id": response.cookies.get("session_id")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual("session deleted", response.text.strip('"'))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from server import create_app


class PipiBackendApiTests(unittest.TestCase):
    """PIPI 백엔드 FastAPI 통합 테스트."""

    def setUp(self) -> None:
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        self.app = create_app(db_path=self.tmp_db.name)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        if os.path.exists(self.tmp_db.name):
            os.unlink(self.tmp_db.name)

    def _request(
        self, method: str, path: str, body=None, token: str | None = None
    ) -> tuple[int, dict]:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = self.client.request(method, path, json=body, headers=headers)
        return resp.status_code, resp.json()

    def test_full_user_lifecycle(self) -> None:
        # 1. Health check
        status, health = self._request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")

        # 2. SignUp
        status, signup_res = self._request(
            "POST", "/api/auth/signup", {"id": "alice", "password": "secret123"}
        )
        self.assertEqual(status, 201)
        token = signup_res["token"]
        self.assertFalse(signup_res["user"]["introSeen"])

        # Duplicate signup blocked
        status, _ = self._request(
            "POST", "/api/auth/signup", {"id": "alice", "password": "secret123"}
        )
        self.assertEqual(status, 409)

        # 3. Intro seen one-time flag
        status, intro = self._request("GET", "/api/intro/status", token=token)
        self.assertEqual(status, 200)
        self.assertFalse(intro["introSeen"])

        status, intro = self._request("POST", "/api/intro/seen", {}, token=token)
        self.assertEqual(status, 200)
        self.assertTrue(intro["introSeen"])

        # 4. Select character & feed / play
        status, char_res = self._request(
            "POST",
            "/api/character",
            {"type": "cat", "color": "#FFFFFF", "name": "눈송이"},
            token=token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(char_res["name"], "눈송이")

        status, fed = self._request("POST", "/api/character/feed", {}, token=token)
        self.assertEqual(status, 200)
        self.assertEqual(fed["snacks"], 4)
        self.assertEqual(fed["exp"], 20)

        status, played = self._request("POST", "/api/character/play", {}, token=token)
        self.assertEqual(status, 200)
        self.assertEqual(played["coins"], 110)
        self.assertEqual(played["exp"], 35)

        # 5. Create task, list tasks, complete task & verify reward
        task_payload = {
            "id": "task_1",
            "title": "영어 공부",
            "durationMin": 60,
            "goal": "",
            "startDate": "2026-11-10T00:00:00",
            "endDate": "2026-11-10T00:00:00",
            "alertBefore": 0,
            "priority": "medium",
            "category": "study",
            "placedDate": "2026-11-10T00:00:00",
            "startTime": "18:00",
            "status": "placed",
        }
        status, created_task = self._request(
            "POST", "/api/tasks", task_payload, token=token
        )
        self.assertEqual(status, 201)
        self.assertEqual(created_task["title"], "영어 공부")

        status, listed = self._request("GET", "/api/tasks", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(len(listed["tasks"]), 1)

        status, completed = self._request(
            "POST",
            "/api/tasks/task_1/complete",
            {"proofImagePath": "photo.jpg"},
            token=token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(completed["status"], "completed")

        # Character received completion reward (+30 EXP, +20 coins, +1 snack)
        status, updated_char = self._request("GET", "/api/character", token=token)
        self.assertEqual(updated_char["exp"], 65)
        self.assertEqual(updated_char["coins"], 130)
        self.assertEqual(updated_char["snacks"], 5)

        # 6. Logout & re-login
        status, _ = self._request("POST", "/api/auth/logout", {}, token=token)
        self.assertEqual(status, 200)
        status, _ = self._request("GET", "/api/character", token=token)
        self.assertEqual(status, 401)

        status, login_res = self._request(
            "POST", "/api/auth/login", {"id": "alice", "password": "secret123"}
        )
        self.assertEqual(status, 200)
        self.assertTrue(login_res["user"]["introSeen"])
        new_token = login_res["token"]

        # 7. Delete account removes everything
        status, _ = self._request("DELETE", "/api/auth/account", token=new_token)
        self.assertEqual(status, 200)
        status, _ = self._request(
            "POST", "/api/auth/login", {"id": "alice", "password": "secret123"}
        )
        self.assertEqual(status, 404)

        # 8. Social login isolates distinct accountId entries
        status, k_res = self._request(
            "POST",
            "/api/auth/social",
            {"provider": "kakao", "accountId": "demo1@kakao.com"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(k_res["user"]["id"], "kakao_demo1@kakao.com")

        status, g_res = self._request(
            "POST",
            "/api/auth/social",
            {"provider": "google", "accountId": "demo2@gmail.com"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(g_res["user"]["id"], "google_demo2@gmail.com")
        self.assertNotEqual(k_res["token"], g_res["token"])


if __name__ == "__main__":
    unittest.main()

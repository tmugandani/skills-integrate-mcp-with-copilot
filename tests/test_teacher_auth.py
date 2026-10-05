import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src import app as app_module


class TeacherAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.teacher_file = Path(self.temp_dir.name) / "teachers.json"
        self.teacher_file.write_text(
            json.dumps({"teacher": app_module.hash_password("correct horse")}),
            encoding="utf-8",
        )
        self.teacher_file_patch = patch.object(
            app_module, "TEACHERS_FILE", self.teacher_file
        )
        self.teacher_file_patch.start()
        self.client = TestClient(app_module.app)
        self.client.cookies.clear()
        app_module.sessions.clear()
        self.participants = app_module.activities["Chess Club"]["participants"].copy()

    def tearDown(self):
        app_module.activities["Chess Club"]["participants"] = self.participants
        app_module.sessions.clear()
        self.client.close()
        self.teacher_file_patch.stop()
        self.temp_dir.cleanup()

    def test_students_can_view_activities_but_cannot_change_registrations(self):
        self.assertEqual(self.client.get("/activities").status_code, 200)
        self.assertEqual(
            self.client.post(
                "/activities/Chess Club/signup", params={"email": "student@test.edu"}
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.delete(
                "/activities/Chess Club/unregister",
                params={"email": self.participants[0]},
            ).status_code,
            401,
        )

    def test_teacher_can_sign_in_and_change_registrations(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "teacher", "password": "correct horse"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies.get(app_module.SESSION_COOKIE))

        signup = self.client.post(
            "/activities/Chess Club/signup", params={"email": "student@test.edu"}
        )
        self.assertEqual(signup.status_code, 200)

        unregister = self.client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "student@test.edu"},
        )
        self.assertEqual(unregister.status_code, 200)

    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "teacher", "password": "incorrect"},
        )
        self.assertEqual(response.status_code, 401)

    def test_missing_teacher_file_is_reported(self):
        self.teacher_file.unlink()
        response = self.client.post(
            "/auth/login",
            json={"username": "teacher", "password": "correct horse"},
        )
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()

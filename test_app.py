"""Offline contract tests: OpenAI is mocked, never billed or contacted."""
import json
import os
import unittest
from unittest.mock import Mock, patch

import requests
from app import app, CATEGORIES


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.env = patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-not-real"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.post = patch("app.requests.post").start()
        self.addCleanup(patch.stopall)

    def provider_result(self, feedback):
        self.post.return_value = Mock(json=lambda: {
            "status": "completed", "output": [{"type": "message", "content": [
                {"type": "output_text", "text": json.dumps({"is_artist_statement": True, **feedback} if isinstance(feedback, dict) else feedback)}]}]})

    def test_status(self):
        self.assertEqual(self.client.get("/").json["status"], "ok")
        self.post.assert_not_called()

    def test_success_and_provider_contract(self):
        feedback = {key: "Consider adding an example in your own words." for key in CATEGORIES}
        self.provider_result(feedback)
        statement = "I use drawings to explore everyday routines."
        response = self.client.post("/feedback", json={"statement": statement})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"feedback": feedback})
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.post.assert_called_once()
        kwargs = self.post.call_args.kwargs
        self.assertEqual(kwargs["json"]["input"], [{"role": "user", "content": statement}])
        self.assertFalse(kwargs["json"]["store"])
        self.assertEqual(kwargs["timeout"], (5, 30))
        self.assertTrue(kwargs["json"]["text"]["format"]["strict"])

    def test_invalid_input_never_calls_provider(self):
        for data in ({}, {"statement": None}, {"statement": 12}, {"statement": []},
                     {"statement": ""}, {"statement": " \n\t"}, [], None,
                     {"statement": "x" * 5001}):
            with self.subTest(data_type=type(data)):
                response = self.client.post("/feedback", data=json.dumps(data), content_type="application/json")
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json)
        self.post.assert_not_called()

    def test_boundary_input(self):
        self.provider_result(dict.fromkeys(CATEGORIES, "Suggestion."))
        self.assertEqual(self.client.post("/feedback", json={"statement": "x" * 5000}).status_code, 200)

    def test_bad_json_and_content_type(self):
        self.assertEqual(self.client.post("/feedback", data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/feedback", data="hello").status_code, 415)
        self.assertEqual(self.client.post("/feedback", data="x" * 65537, content_type="application/json").status_code, 413)
        self.post.assert_not_called()

    def test_missing_configuration(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            self.assertEqual(self.client.post("/feedback", json={"statement": "My art."}).status_code, 503)
        self.post.assert_not_called()

    def test_provider_failures_hide_details(self):
        for exception, expected in [(requests.Timeout("SECRET"), 504),
                                    (requests.ConnectionError("SECRET"), 502),
                                    (requests.HTTPError("SECRET"), 502)]:
            self.post.side_effect = exception
            response = self.client.post("/feedback", json={"statement": "My art."})
            self.assertEqual(response.status_code, expected)
            self.assertNotIn("SECRET", response.get_data(as_text=True))

    def test_invalid_provider_output(self):
        for value in ({"clarity": "Only one"}, dict.fromkeys(CATEGORIES, " "),
                      {**dict.fromkeys(CATEGORIES, "Suggestion"), "extra": "No"}, [],
                      dict.fromkeys(CATEGORIES, 4)):
            self.provider_result(value)
            self.assertEqual(self.client.post("/feedback", json={"statement": "My art."}).status_code, 502)
        self.post.return_value.json.side_effect = ValueError("SECRET")
        self.assertEqual(self.client.post("/feedback", json={"statement": "My art."}).status_code, 502)

    def test_refusal_and_incomplete(self):
        for payload, expected in [({"status": "incomplete"}, 502),
            ({"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal"}]}]}, 422)]:
            self.post.return_value = Mock(json=lambda: payload)
            self.assertEqual(self.client.post("/feedback", json={"statement": "My art."}).status_code, expected)

    def test_quota_error_explains_required_action(self):
        response = Mock(status_code=429)
        response.json.return_value = {"error": {"type": "insufficient_quota", "message": "SECRET"}}
        self.post.side_effect = requests.HTTPError(response=response)
        result = self.client.post("/feedback", json={"statement": "My art."})
        self.assertEqual(result.status_code, 503)
        self.assertIn("billing", result.json["error"])
        self.assertNotIn("SECRET", result.get_data(as_text=True))

    def test_insufficient_input(self):
        for statement in ("hi", "Please tell me the weather"):
            self.provider_result({"is_artist_statement": False, **dict.fromkeys(CATEGORIES, None)})
            response = self.client.post("/feedback", json={"statement": statement})
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json["code"], "insufficient_input")
            self.assertNotIn("feedback", response.json)

    def test_short_meaningful_statement(self):
        self.provider_result(dict.fromkeys(CATEGORIES, "Consider describing your drawn trees."))
        response = self.client.post("/feedback", json={"statement": "I draw trees."})
        self.assertEqual(response.status_code, 200)

    def test_reject_inconsistent_insufficient_result(self):
        self.provider_result({"is_artist_statement": False, **dict.fromkeys(CATEGORIES, "Invented")})
        self.assertEqual(self.client.post("/feedback", json={"statement": "hi"}).status_code, 502)

    def test_cors(self):
        for origin in ("http://localhost:8000", "http://127.0.0.1:8000", "https://fatimajshah.github.io"):
            response = self.client.options("/feedback", headers={"Origin": origin,
                "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"})
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)
            self.assertIn("POST", response.headers["Access-Control-Allow-Methods"])
        response = self.client.options("/feedback", headers={"Origin": "https://unrelated.example"})
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)


if __name__ == "__main__":
    unittest.main()

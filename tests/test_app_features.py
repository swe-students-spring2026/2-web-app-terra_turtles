import os
import re
import unittest
from datetime import datetime, timedelta

from bson import ObjectId

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/test")

import app as app_module


def _matches(doc, query):
    for key, expected in (query or {}).items():
        actual = doc.get(key)
        if isinstance(expected, dict):
            if "$gte" in expected and (actual is None or actual < expected["$gte"]):
                return False
            if "$regex" in expected:
                flags = 0
                if expected.get("$options") == "i":
                    flags |= re.IGNORECASE
                if not re.search(expected["$regex"], str(actual or ""), flags):
                    return False
        elif actual != expected:
            return False
    return True


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction):
        reverse = direction == -1
        self.docs.sort(key=lambda d: d.get(key), reverse=reverse)
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    def __iter__(self):
        return iter(self.docs)


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    def find(self, query=None):
        return FakeCursor([d for d in self.docs if _matches(d, query or {})])

    def find_one(self, query=None):
        for d in self.docs:
            if _matches(d, query or {}):
                return d
        return None

    def count_documents(self, query=None):
        return len([d for d in self.docs if _matches(d, query or {})])

    def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.docs.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})

    def update_one(self, query, update, upsert=False):
        doc = self.find_one(query)
        if doc is None and upsert:
            doc = dict(query)
            for k, v in update.get("$setOnInsert", {}).items():
                doc[k] = v
            for k, v in update.get("$set", {}).items():
                doc[k] = v
            self.insert_one(doc)
            return
        if doc is None:
            return
        for k, v in update.get("$set", {}).items():
            doc[k] = v

    def delete_one(self, query):
        for i, d in enumerate(self.docs):
            if _matches(d, query):
                self.docs.pop(i)
                return


class FakeDB:
    def __init__(self, data):
        self._collections = {name: FakeCollection(docs) for name, docs in data.items()}

    def __getitem__(self, key):
        if key not in self._collections:
            self._collections[key] = FakeCollection([])
        return self._collections[key]


class AppFeaturesTests(unittest.TestCase):
    def setUp(self):
        self.user_id = ObjectId()
        self.user_doc = {
            "_id": self.user_id,
            "name": "Peter",
            "email": "peter@example.com",
            "age": 22,
            "sex": "male",
        }
        self.today = datetime.now().date().isoformat()
        self.yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()

        fake_db = FakeDB(
            {
                "users": [self.user_doc],
                "sets": [],
                "meals": [],
                "weights": [],
                "goals": [],
            }
        )
        app_module.db = fake_db
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(self.user_id)
            sess["_fresh"] = True

    def test_workouts_defaults_to_today(self):
        app_module.db["sets"].insert_one(
            {
                "user_id": str(self.user_id),
                "date": self.today,
                "exercise": "bench press",
                "sets": 3,
                "reps": 5,
                "weight": 100.0,
            }
        )
        app_module.db["sets"].insert_one(
            {
                "user_id": str(self.user_id),
                "date": self.yesterday,
                "exercise": "deadlift",
                "sets": 3,
                "reps": 5,
                "weight": 180.0,
            }
        )

        res = self.client.get("/workouts")
        body = res.get_data(as_text=True)

        self.assertEqual(200, res.status_code)
        self.assertIn("bench press", body)
        self.assertNotIn("deadlift", body)
        self.assertIn(f'value="{self.today}"', body)

    def test_diet_defaults_to_today(self):
        app_module.db["meals"].insert_one(
            {
                "user_id": str(self.user_id),
                "date": self.today,
                "meal": "chicken bowl",
                "calories": 550,
                "protein": 45,
                "carbs": 50,
                "fats": 12,
            }
        )
        app_module.db["meals"].insert_one(
            {
                "user_id": str(self.user_id),
                "date": self.yesterday,
                "meal": "pizza",
                "calories": 900,
                "protein": 30,
                "carbs": 90,
                "fats": 40,
            }
        )

        res = self.client.get("/diet")
        body = res.get_data(as_text=True)

        self.assertEqual(200, res.status_code)
        self.assertIn("chicken bowl", body)
        self.assertNotIn("pizza", body)
        self.assertIn(f'value="{self.today}"', body)

    def test_goals_saved_and_shown_on_home(self):
        app_module.db["sets"].insert_one(
            {
                "user_id": str(self.user_id),
                "date": self.today,
                "exercise": "squat",
                "sets": 3,
                "reps": 8,
                "weight": 140.0,
            }
        )
        app_module.db["meals"].insert_one(
            {
                "user_id": str(self.user_id),
                "date": self.today,
                "meal": "salmon",
                "calories": 600,
                "protein": 50,
                "carbs": 20,
                "fats": 18,
            }
        )

        post_res = self.client.post(
            "/goals",
            data={
                "workouts_per_day": "2",
                "calories_per_day": "2000",
                "protein_g_per_day": "140",
            },
            follow_redirects=True,
        )
        home_res = self.client.get("/")
        body = home_res.get_data(as_text=True)

        self.assertEqual(200, post_res.status_code)
        self.assertEqual(200, home_res.status_code)
        self.assertIn("Daily Goals", body)
        self.assertIn("Workouts: 1 / 2", body)
        self.assertIn("Calories: 600 / 2000", body)
        self.assertIn("Protein: 50 / 140 g", body)


if __name__ == "__main__":
    unittest.main()

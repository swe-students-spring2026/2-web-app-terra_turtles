"""
Tests for FitFlow Flask app.
MongoDB is fully mocked — no live database required.
Run: .venv/bin/pytest test_app.py -v
"""
import os
import pytest
from unittest.mock import MagicMock, patch
from bson import ObjectId
from werkzeug.security import generate_password_hash


# ── Patch MongoDB before importing app ───────────────────────────────────────
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DBNAME", "test_db")
os.environ.setdefault("SECRET_KEY", "test-secret")

# Patch MongoClient so app.py never actually connects
_mock_client = MagicMock()
_mock_db = MagicMock()
_mock_client.__getitem__.return_value = _mock_db

with patch("pymongo.MongoClient", return_value=_mock_client):
    import app as flask_app  # noqa: E402  (import after patching)

# Replace the live db reference used throughout routes
flask_app.db = _mock_db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.app.test_client() as c:
        yield c


def _fake_user(sex="male", age=25):
    uid = ObjectId()
    return {
        "_id": uid,
        "name": "Test User",
        "email": "test@example.com",
        "password_hash": generate_password_hash("password123", method="pbkdf2:sha256"),
        "sex": sex,
        "age": age,
    }


def _make_col(user_doc):
    """Return a MagicMock collection that always resolves find_one to user_doc
    and returns empty cursors for find()."""
    col = MagicMock()
    col.find_one.return_value = user_doc

    cursor = MagicMock()
    cursor.__iter__ = MagicMock(return_value=iter([]))
    find_result = MagicMock()
    find_result.sort.return_value = find_result
    find_result.limit.return_value = cursor
    col.find.return_value = find_result
    col.count_documents.return_value = 0
    col.insert_one.return_value = MagicMock(inserted_id=ObjectId())
    col.update_one.return_value = MagicMock()
    col.delete_one.return_value = MagicMock()
    return col


def _patch_db(user_doc):
    """Patch flask_app.db so all collection lookups use a col backed by user_doc."""
    col = _make_col(user_doc)
    mock_db = MagicMock()
    mock_db.__getitem__.return_value = col
    return mock_db, col


# ── Helper / pure-function tests ──────────────────────────────────────────────

class TestHelpers:
    def test_to_int_valid(self):
        assert flask_app.to_int("42") == 42

    def test_to_int_invalid(self):
        assert flask_app.to_int("abc") == 0

    def test_to_int_default(self):
        assert flask_app.to_int(None, default=7) == 7

    def test_to_float_valid(self):
        assert flask_app.to_float("3.14") == pytest.approx(3.14)

    def test_to_float_invalid(self):
        assert flask_app.to_float("xyz") == 0.0

    def test_to_oid_valid(self):
        oid = ObjectId()
        assert flask_app.to_oid(str(oid)) == oid

    def test_to_oid_invalid(self):
        assert flask_app.to_oid("not-an-oid") is None


class TestBmiTag:
    def test_none(self):
        assert flask_app.bmi_tag(None) == ""

    def test_underweight(self):
        assert flask_app.bmi_tag(17.0) == "Underweight"

    def test_normal(self):
        assert flask_app.bmi_tag(22.0) == "Normal"

    def test_overweight(self):
        assert flask_app.bmi_tag(27.5) == "Overweight"

    def test_obese(self):
        assert flask_app.bmi_tag(32.0) == "Obese"

    def test_boundary_18_5(self):
        assert flask_app.bmi_tag(18.5) == "Normal"

    def test_boundary_25(self):
        assert flask_app.bmi_tag(25.0) == "Overweight"

    def test_boundary_30(self):
        assert flask_app.bmi_tag(30.0) == "Obese"


class TestBmiCssModifier:
    def test_none(self):
        assert flask_app.bmi_css_modifier(None) == ""

    def test_under(self):
        assert flask_app.bmi_css_modifier(16.0) == "under"

    def test_normal(self):
        assert flask_app.bmi_css_modifier(21.0) == "normal"

    def test_over(self):
        assert flask_app.bmi_css_modifier(27.0) == "over"

    def test_obese(self):
        assert flask_app.bmi_css_modifier(35.0) == "obese"


class TestComputeWeightMetrics:
    def test_missing_inputs_returns_nones(self):
        result = flask_app.compute_weight_metrics(None, 175, 25, "male")
        assert result == {"bmi": None, "bmr": None, "ibw": None, "body_fat_pct": None}

    def test_missing_sex(self):
        result = flask_app.compute_weight_metrics(70, 175, 25, None)
        assert result["bmi"] is None

    def test_bmi_calculation_male(self):
        # 70 kg / (1.75 m)^2 = 22.9
        result = flask_app.compute_weight_metrics(70, 175, 25, "male")
        assert result["bmi"] == pytest.approx(22.9, abs=0.1)

    def test_bmi_calculation_female(self):
        result = flask_app.compute_weight_metrics(60, 165, 30, "female")
        expected_bmi = round(60 / (1.65 ** 2), 1)
        assert result["bmi"] == expected_bmi

    def test_bmr_male(self):
        # 10*70 + 6.25*175 - 5*25 + 5 = 700 + 1093.75 - 125 + 5 = 1673.75 → 1674
        result = flask_app.compute_weight_metrics(70, 175, 25, "male")
        assert result["bmr"] == 1674

    def test_bmr_female(self):
        # 10*60 + 6.25*165 - 5*30 - 161 = 600 + 1031.25 - 150 - 161 = 1320.25 → 1320
        result = flask_app.compute_weight_metrics(60, 165, 30, "female")
        assert result["bmr"] == 1320

    def test_ibw_male_above_60in(self):
        # 175 cm / 2.54 = 68.9 in  → 50 + 2.3*(68.9-60) = 50 + 20.47 = 70.5
        result = flask_app.compute_weight_metrics(70, 175, 25, "male")
        assert result["ibw"] == pytest.approx(70.5, abs=0.2)

    def test_ibw_female_above_60in(self):
        # 165 cm / 2.54 = 64.96 in → 45.5 + 2.3*(64.96-60) = 45.5 + 11.41 = 56.9
        result = flask_app.compute_weight_metrics(60, 165, 30, "female")
        assert result["ibw"] == pytest.approx(56.9, abs=0.2)

    def test_ibw_none_below_60in(self):
        # 150 cm = 59.06 in (below 60)
        result = flask_app.compute_weight_metrics(50, 150, 25, "male")
        assert result["ibw"] is None

    def test_body_fat_pct_non_negative(self):
        # Very muscular / low BMI person shouldn't get a negative value
        result = flask_app.compute_weight_metrics(60, 185, 20, "male")
        assert result["body_fat_pct"] >= 0.0

    def test_body_fat_pct_male_formula(self):
        result = flask_app.compute_weight_metrics(70, 175, 25, "male")
        bmi = result["bmi"]
        expected = max(0.0, round(1.20 * bmi + 0.23 * 25 - 16.2, 1))
        assert result["body_fat_pct"] == expected

    def test_body_fat_pct_female_formula(self):
        result = flask_app.compute_weight_metrics(60, 165, 30, "female")
        bmi = result["bmi"]
        expected = max(0.0, round(1.20 * bmi + 0.23 * 30 - 5.4, 1))
        assert result["body_fat_pct"] == expected


# ── Auth route tests ───────────────────────────────────────────────────────────

class TestAuthRoutes:
    def test_login_page_get(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        with patch.object(flask_app, "db", mock_db):
            resp = client.get("/login")
        assert resp.status_code == 200

    def test_register_page_get(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        col.find_one.return_value = None
        with patch.object(flask_app, "db", mock_db):
            resp = client.get("/register")
        assert resp.status_code == 200

    def test_register_post_missing_fields(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/register", data={"email": "", "password": ""})
        assert resp.status_code == 200
        assert b"required" in resp.data

    def test_register_post_password_mismatch(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        col.find_one.return_value = None
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/register", data={
                "email": "a@b.com", "password": "abc123", "confirm": "different"
            })
        assert b"match" in resp.data

    def test_register_post_short_password(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        col.find_one.return_value = None
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/register", data={
                "email": "a@b.com", "password": "abc", "confirm": "abc"
            })
        assert b"6 characters" in resp.data

    def test_login_post_wrong_password(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/login", data={"email": "test@example.com", "password": "wrong"})
        assert b"Invalid" in resp.data

    def test_login_post_unknown_email(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        col.find_one.return_value = None
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/login", data={"email": "no@one.com", "password": "pass"})
        assert b"Invalid" in resp.data


# ── Protected route redirect tests (unauthenticated) ─────────────────────────

class TestUnauthenticatedRedirects:
    @pytest.mark.parametrize("path", [
        "/workouts", "/diet", "/weights", "/weights/new",
        "/profile", "/bmi",
    ])
    def test_redirect_to_login(self, client, path):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        col.find_one.return_value = None  # not logged in
        with patch.object(flask_app, "db", mock_db):
            resp = client.get(path)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_timer_public(self, client):
        """Timer page is publicly accessible (no @login_required)."""
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        with patch.object(flask_app, "db", mock_db):
            resp = client.get("/timer")
        assert resp.status_code == 200


# ── Weights route tests (authenticated) ──────────────────────────────────────

class TestWeightsRoutes:
    def _login(self, client, user_doc, mock_db):
        """Log in via the login POST; mock_db must be patched for this call."""
        with patch.object(flask_app, "db", mock_db):
            client.post(
                "/login",
                data={"email": user_doc["email"], "password": "password123"},
                follow_redirects=False,
            )

    def test_weights_page_loads(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.get("/weights")
        assert resp.status_code == 200

    def test_weights_new_get(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.get("/weights/new")
        assert resp.status_code == 200

    def test_weights_new_post_missing_fields(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/weights/new", data={"date": "2026-01-01"})
        assert resp.status_code == 200
        assert b"required" in resp.data

    def test_weights_new_post_valid(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/weights/new", data={
                "date": "2026-01-15", "weight_kg": "72.5", "height_cm": "175"
            }, follow_redirects=False)
        assert resp.status_code == 302
        assert "/weights" in resp.headers["Location"]

    def test_weights_delete_invalid_id(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.get("/weights/not-an-oid/delete")
        assert resp.status_code == 400

    def test_weights_delete_not_found(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        # After login, make weights collection return None for find_one
        weights_col = _make_col(user_doc)
        weights_col.find_one.return_value = None

        def col_by_name(name):
            if name == "weights":
                return weights_col
            return col
        mock_db.__getitem__.side_effect = col_by_name

        with patch.object(flask_app, "db", mock_db):
            resp = client.get(f"/weights/{ObjectId()}/delete")
        assert resp.status_code == 404

    def test_weights_delete_post_redirects(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.post(f"/weights/{ObjectId()}/delete", follow_redirects=False)
        assert resp.status_code == 302
        assert "/weights" in resp.headers["Location"]


# ── Profile route tests ────────────────────────────────────────────────────────

class TestProfileRoutes:
    def _login(self, client, user_doc, mock_db):
        with patch.object(flask_app, "db", mock_db):
            client.post(
                "/login",
                data={"email": user_doc["email"], "password": "password123"},
                follow_redirects=False,
            )

    def test_profile_get(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.get("/profile")
        assert resp.status_code == 200

    def test_profile_post_invalid_sex(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/profile", data={"age": "25", "sex": "unknown"})
        assert resp.status_code == 200
        assert b"valid sex" in resp.data

    def test_profile_post_invalid_age(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/profile", data={"age": "999", "sex": "male"})
        assert resp.status_code == 200
        assert b"valid age" in resp.data

    def test_profile_post_valid_redirects(self, client):
        user_doc = _fake_user()
        mock_db, col = _patch_db(user_doc)
        self._login(client, user_doc, mock_db)
        with patch.object(flask_app, "db", mock_db):
            resp = client.post("/profile", data={"age": "28", "sex": "female"},
                               follow_redirects=False)
        assert resp.status_code == 302
        assert "/profile" in resp.headers["Location"]

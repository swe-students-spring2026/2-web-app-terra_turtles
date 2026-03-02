import os
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import certifi
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("MONGO_DBNAME", "gym_info")

if not mongo_uri:
    raise RuntimeError("MONGO_URI is not set in .env")

client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
db = client[db_name]

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc["_id"])
        self.name = user_doc.get("name", "")
        self.email = user_doc.get("email", "")


@login_manager.user_loader
def load_user(user_id):
    user_doc = db["users"].find_one({"_id": ObjectId(user_id)})
    if user_doc:
        return User(user_doc)
    return None


# Helpers
def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def require_login():
    return session.get("user_id") is not None


def current_user_id():
    return session.get("user_id")


@app.get("/")
def home():
    if not current_user.is_authenticated:
        return render_template(
            "home.html",
            today_workouts=0,
            today_calories=0,
            today_protein=0,
            recent_workouts=[]
        )

    uid = current_user.id
    today = datetime.now().date().isoformat()

    today_workouts = db["sets"].count_documents({"user_id": uid, "date": today})

    meals_today = list(db["meals"].find({"user_id": uid, "date": today}))
    today_calories = sum(to_int(m.get("calories")) for m in meals_today)
    today_protein = sum(to_int(m.get("protein")) for m in meals_today)

    recent_workouts = list(
        db["sets"].find({"user_id": uid}).sort("_id", -1).limit(7)
    )

    return render_template(
        "home.html",
        today_workouts=today_workouts,
        today_calories=today_calories,
        today_protein=today_protein,
        recent_workouts=recent_workouts
    )


# Auth
@app.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("register.html")


@app.post("/register")
def register_post():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""

    if not email or not password:
        return render_template("register.html", error="Email and password are required.")

    if password != confirm:
        return render_template("register.html", error="Passwords do not match.")

    if len(password) < 6:
        return render_template("register.html", error="Password must be at least 6 characters.")

    if db["users"].find_one({"email": email}):
        return render_template("register.html", error="Email already registered.")

    result = db["users"].insert_one({
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password, method="pbkdf2:sha256"),
        "created_at": datetime.utcnow(),
    })

    user_doc = db["users"].find_one({"_id": result.inserted_id})
    login_user(User(user_doc))
    return redirect(url_for("home"))


@app.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("login.html")


@app.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    user_doc = db["users"].find_one({"email": email})
    if not user_doc or not check_password_hash(user_doc.get("password_hash", ""), password):
        return render_template("login.html", error="Invalid email or password.")

    login_user(User(user_doc))
    return redirect(url_for("home"))


@app.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# Forgot / Reset password
serializer = URLSafeTimedSerializer(app.secret_key)


@app.get("/forgot-password")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("forgot_password.html")


@app.post("/forgot-password")
def forgot_password_post():
    email = (request.form.get("email") or "").strip().lower()

    user_doc = db["users"].find_one({"email": email})
    if not user_doc:
        return render_template("forgot_password.html", error="No account found with that email.")

    token = serializer.dumps(email, salt="reset-password")
    return redirect(url_for("reset_password", token=token))


@app.get("/reset-password/<token>")
def reset_password(token):
    try:
        email = serializer.loads(token, salt="reset-password", max_age=900)
    except (SignatureExpired, BadSignature):
        return render_template("forgot_password.html", error="Reset link is invalid or has expired.")

    return render_template("reset_password.html", token=token, email=email)


@app.post("/reset-password/<token>")
def reset_password_post(token):
    try:
        email = serializer.loads(token, salt="reset-password", max_age=900)
    except (SignatureExpired, BadSignature):
        return render_template("forgot_password.html", error="Reset link is invalid or has expired.")

    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""

    if len(password) < 6:
        return render_template("reset_password.html", token=token, email=email, error="Password must be at least 6 characters.")

    if password != confirm:
        return render_template("reset_password.html", token=token, email=email, error="Passwords do not match.")

    db["users"].update_one(
        {"email": email},
        {"$set": {"password_hash": generate_password_hash(password, method="pbkdf2:sha256")}}
    )

    return redirect(url_for("login"))


# Workouts (sets)
@app.get("/workouts")
@login_required
def workouts():
    workouts = list(db["sets"].find({"user_id": current_user.id}).sort("_id", -1))
    return render_template("workouts.html", workouts=workouts)


@app.get("/workouts/search")
@login_required
def workouts_search():
    q = (request.args.get("q") or "").strip()
    query = {"user_id": current_user.id}

    if q:
        query["exercise"] = {"$regex": q, "$options": "i"}

    workouts = list(db["sets"].find(query).sort("_id", -1))
    return render_template("workouts.html", workouts=workouts, q=q)


@app.get("/workouts/new")
@login_required
def workout_new():
    return render_template("workout_new.html")


@app.post("/workouts/new")
@login_required
def workout_new_post():
    doc = {
        "user_id": current_user.id,
        "date": request.form.get("date"),
        "exercise": (request.form.get("exercise") or "").strip(),
        "sets": to_int(request.form.get("sets")),
        "reps": to_int(request.form.get("reps")),
        "weight": to_float(request.form.get("weight")),
        "notes": (request.form.get("notes") or "").strip(),
        "created_at": datetime.utcnow(),
    }
    db["sets"].insert_one(doc)
    return redirect(url_for("workouts"))


@app.get("/workouts/<id>/edit")
@login_required
def workout_edit(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid workout id", 400

    workout = db["sets"].find_one({"_id": _id, "user_id": current_user.id})
    if not workout:
        return "Workout not found", 404

    return render_template("workout_edit.html", workout=workout)


@app.post("/workouts/<id>/edit")
@login_required
def workout_edit_post(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid workout id", 400

    db["sets"].update_one(
        {"_id": _id, "user_id": current_user.id},
        {"$set": {
            "date": request.form.get("date"),
            "exercise": (request.form.get("exercise") or "").strip(),
            "sets": to_int(request.form.get("sets")),
            "reps": to_int(request.form.get("reps")),
            "weight": to_float(request.form.get("weight")),
            "notes": (request.form.get("notes") or "").strip(),
            "updated_at": datetime.utcnow(),
        }}
    )
    return redirect(url_for("workouts"))


@app.get("/workouts/<id>/delete")
@login_required
def workout_delete(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid workout id", 400

    workout = db["sets"].find_one({"_id": _id, "user_id": current_user.id})
    if not workout:
        return "Workout not found", 404

    return render_template("workout_delete.html", workout=workout)


@app.post("/workouts/<id>/delete")
@login_required
def workout_delete_post(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid workout id", 400

    db["sets"].delete_one({"_id": _id, "user_id": current_user.id})
    return redirect(url_for("workouts"))


# Diet (meals)
def meal_totals(meals):
    return {
        "calories": sum(to_int(m.get("calories")) for m in meals),
        "protein": sum(to_int(m.get("protein")) for m in meals),
        "carbs": sum(to_int(m.get("carbs")) for m in meals),
        "fats": sum(to_int(m.get("fats")) for m in meals),
    }


@app.get("/diet")
@login_required
def diet():
    date = (request.args.get("date") or "").strip()
    query = {"user_id": current_user.id}

    if date:
        query["date"] = date

    meals = list(db["meals"].find(query).sort("_id", -1))
    totals = meal_totals(meals)
    return render_template("diet.html", meals=meals, totals=totals, date=date)


@app.get("/diet/search")
@login_required
def diet_search():
    q = (request.args.get("q") or "").strip()
    query = {"user_id": current_user.id}

    if q:
        query["meal"] = {"$regex": q, "$options": "i"}

    meals = list(db["meals"].find(query).sort("_id", -1))
    totals = meal_totals(meals)
    return render_template("diet.html", meals=meals, totals=totals, q=q)


@app.get("/diet/new")
@login_required
def diet_new():
    return render_template("diet_new.html")


@app.post("/diet/new")
@login_required
def diet_new_post():
    doc = {
        "user_id": current_user.id,
        "date": request.form.get("date"),
        "meal": (request.form.get("meal") or "").strip(),
        "calories": to_int(request.form.get("calories")),
        "protein": to_int(request.form.get("protein")),
        "carbs": to_int(request.form.get("carbs")),
        "fats": to_int(request.form.get("fats")),
        "notes": (request.form.get("notes") or "").strip(),
        "created_at": datetime.utcnow(),
    }
    db["meals"].insert_one(doc)
    return redirect(url_for("diet"))


@app.get("/diet/<id>/delete")
@login_required
def diet_delete(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid meal id", 400

    meal = db["meals"].find_one({"_id": _id, "user_id": current_user.id})
    if not meal:
        return "Meal not found", 404

    return render_template("diet_delete.html", meal=meal)


@app.post("/diet/<id>/delete")
@login_required
def diet_delete_post(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid meal id", 400

    db["meals"].delete_one({"_id": _id, "user_id": current_user.id})
    return redirect(url_for("diet"))


# Timer
@app.get("/timer")
def timer():
    return render_template("timer.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
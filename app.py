import os
from datetime import datetime, timedelta
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
        self.sex = user_doc.get("sex", None)
        self.age = user_doc.get("age", None)


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


def compute_weight_metrics(weight_kg, height_cm, age, sex):
    if not all([weight_kg, height_cm, age, sex]):
        return {"bmi": None, "bmr": None, "ibw": None, "body_fat_pct": None}
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)
    if sex == "male":
        bmr = round(10 * weight_kg + 6.25 * height_cm - 5 * age + 5)
    else:
        bmr = round(10 * weight_kg + 6.25 * height_cm - 5 * age - 161)
    height_in = height_cm / 2.54
    if height_in >= 60:
        ibw = round(50 + 2.3 * (height_in - 60), 1) if sex == "male" else round(45.5 + 2.3 * (height_in - 60), 1)
    else:
        ibw = None
    if sex == "male":
        body_fat_pct = round(1.20 * bmi + 0.23 * age - 16.2, 1)
    else:
        body_fat_pct = round(1.20 * bmi + 0.23 * age - 5.4, 1)
    body_fat_pct = max(0.0, body_fat_pct)
    return {"bmi": bmi, "bmr": int(bmr), "ibw": ibw, "body_fat_pct": body_fat_pct}


def bmi_tag(bmi):
    if bmi is None:
        return ""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25.0:
        return "Normal"
    elif bmi < 30.0:
        return "Overweight"
    return "Obese"


def bmi_css_modifier(bmi):
    if bmi is None:
        return ""
    if bmi < 18.5:
        return "under"
    elif bmi < 25.0:
        return "normal"
    elif bmi < 30.0:
        return "over"
    return "obese"


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
            recent_workouts=[],
            calories_data=[]
        )

    uid = current_user.id
    today = datetime.now().date().isoformat()

    thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()

    meals_monthly = list(db["meals"].find({"user_id": uid, "date": {"$gte": thirty_days_ago}}))
    
    # Group by date and sum calories
    daily_totals = {}
    for meal in meals_monthly:
        date = meal.get("date")
        cals = to_int(meal.get("calories"))
        if date:
            daily_totals[date] = daily_totals.get(date, 0) + cals
    
    # Convert to list of dicts, sorted by date
    calories_data = [
        {"date": date, "calories": cals}
        for date, cals in sorted(daily_totals.items())
    ]

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
        recent_workouts=recent_workouts,
        calories_data=calories_data
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


# Profile
@app.get("/profile")
@login_required
def profile():
    user_doc = db["users"].find_one({"_id": to_oid(current_user.id)})
    return render_template("profile.html", user=user_doc)


@app.post("/profile")
@login_required
def profile_post():
    age = to_int(request.form.get("age"))
    sex = (request.form.get("sex") or "").strip().lower()
    user_doc = db["users"].find_one({"_id": to_oid(current_user.id)})

    if sex not in ("male", "female"):
        return render_template("profile.html", user=user_doc, error="Please select a valid sex.")
    if not (1 <= age <= 120):
        return render_template("profile.html", user=user_doc, error="Please enter a valid age (1–120).")

    db["users"].update_one(
        {"_id": to_oid(current_user.id)},
        {"$set": {"age": age, "sex": sex, "updated_at": datetime.utcnow()}}
    )
    return redirect(url_for("profile"))


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
    today = datetime.now().date().isoformat()

    # active_date decides summary and target calculations
    active_date = date if date else today

    # list meals behavior: if date provided, show meals for that date; if no date, show all meals (sorted by date desc)
    query = {"user_id": current_user.id}
    if date:
        query["date"] = date

    meals = list(db["meals"].find(query).sort("_id", -1))

    # totals always computed from active_date
    meals_active = list(db["meals"].find({"user_id": current_user.id, "date": active_date}))
    totals = meal_totals(meals_active)

    return render_template(
        "diet.html",
        meals=meals,
        totals=totals,
        date=date,
        today=today,
        active_date=active_date
    )


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

@app.get("/diet/<id>/edit")
@login_required
def diet_edit(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid meal id", 400

    meal = db["meals"].find_one({"_id": _id, "user_id": current_user.id})
    if not meal:
        return "Meal not found", 404

    return render_template("diet_edit.html", meal=meal)


@app.post("/diet/<id>/edit")
@login_required
def diet_edit_post(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid meal id", 400

    db["meals"].update_one(
        {"_id": _id, "user_id": current_user.id},
        {"$set": {
            "date": request.form.get("date"),
            "meal": (request.form.get("meal") or "").strip(),
            "calories": to_int(request.form.get("calories")),
            "protein": to_int(request.form.get("protein")),
            "carbs": to_int(request.form.get("carbs")),
            "fats": to_int(request.form.get("fats")),
            "notes": (request.form.get("notes") or "").strip(),
            "updated_at": datetime.utcnow(),
        }}
    )
    return redirect(url_for("diet"))

# Weights
@app.get("/weights")
@login_required
def weights():
    uid = current_user.id
    age = current_user.age
    sex = current_user.sex

    entries = list(db["weights"].find({"user_id": uid}).sort("created_at", -1).limit(50))
    for e in entries:
        metrics = compute_weight_metrics(e.get("weight_kg"), e.get("height_cm"), age, sex)
        e["bmi"] = metrics["bmi"]
        e["bmr"] = metrics["bmr"]
        e["ibw"] = metrics["ibw"]
        e["body_fat_pct"] = metrics["body_fat_pct"]
        e["bmi_tag"] = bmi_tag(metrics["bmi"])
        e["bmi_mod"] = bmi_css_modifier(metrics["bmi"])

    latest = entries[0] if entries else None

    chart_entries = list(db["weights"].find({"user_id": uid}).sort("created_at", 1).limit(30))
    weights_data = [{"date": e["date"], "weight": e["weight_kg"]} for e in chart_entries]

    profile_complete = bool(age and sex)
    return render_template("weights.html", entries=entries, latest=latest,
                           weights_data=weights_data, profile_complete=profile_complete)


@app.get("/weights/new")
@login_required
def weights_new():
    today = datetime.now().date().isoformat()
    profile_complete = bool(current_user.age and current_user.sex)
    return render_template("weights_new.html", today=today, profile_complete=profile_complete)


@app.post("/weights/new")
@login_required
def weights_new_post():
    weight_kg = to_float(request.form.get("weight_kg"))
    height_cm = to_float(request.form.get("height_cm"))
    date = request.form.get("date") or datetime.now().date().isoformat()
    notes = (request.form.get("notes") or "").strip()

    if not weight_kg or not height_cm:
        today = datetime.now().date().isoformat()
        return render_template("weights_new.html", today=today,
                               profile_complete=bool(current_user.age and current_user.sex),
                               error="Weight and height are required.")

    db["weights"].insert_one({
        "user_id": current_user.id,
        "date": date,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "notes": notes,
        "created_at": datetime.utcnow(),
    })
    return redirect(url_for("weights"))


@app.get("/weights/<id>/delete")
@login_required
def weights_delete(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid entry id", 400
    entry = db["weights"].find_one({"_id": _id, "user_id": current_user.id})
    if not entry:
        return "Entry not found", 404
    return render_template("weights_delete.html", entry=entry)


@app.post("/weights/<id>/delete")
@login_required
def weights_delete_post(id):
    _id = to_oid(id)
    if not _id:
        return "Invalid entry id", 400
    db["weights"].delete_one({"_id": _id, "user_id": current_user.id})
    return redirect(url_for("weights"))


# BMI
@app.get("/bmi")
@login_required
def bmi():
    return render_template("bmi.html")


# Recipes
@app.get("/recipes")
@login_required
def recipes():
    dish = (request.args.get("dish") or "beef-bowl").strip()

    recipes_data = {
        "beef-bowl": {
            "title": "Beef Bowl",
            "macros": {"calories": 650, "protein": 42, "carbs": 70, "fats": 22},
            "ingredients": [
                "150g lean ground beef",
                "1 cup cooked rice",
                "1/2 onion",
                "1 tbsp soy sauce",
                "1 tsp sugar",
                "1 tsp oil",
                "Salt, black pepper",
            ],
            "steps": [
                "Cook rice and set aside.",
                "Slice onion. Heat oil on medium heat.",
                "Cook onion 2–3 minutes until soft.",
                "Add beef and cook until browned.",
                "Add soy sauce and sugar, stir 30 seconds.",
                "Serve over rice.",
            ],
        },
        "chicken-bowl": {
            "title": "Chicken Bowl",
            "macros": {"calories": 560, "protein": 48, "carbs": 60, "fats": 14},
            "ingredients": [
                "180g chicken breast",
                "1 cup cooked rice",
                "1 tbsp soy sauce",
                "1 tsp oil",
                "Salt, black pepper",
            ],
            "steps": [
                "Season chicken with salt and pepper.",
                "Heat oil on medium heat.",
                "Cook chicken until done, then slice.",
                "Serve over rice with a light soy drizzle.",
            ],
        },
        "caesar-salad": {
            "title": "Caesar Salad",
            "macros": {"calories": 430, "protein": 28, "carbs": 20, "fats": 28},
            "ingredients": [
                "2 cups romaine lettuce",
                "120g cooked chicken",
                "20g croutons",
                "2 tbsp Caesar dressing",
                "Parmesan (optional)",
            ],
            "steps": [
                "Wash and chop romaine.",
                "Slice chicken.",
                "Combine lettuce, chicken, and croutons.",
                "Add dressing and toss.",
                "Add parmesan if desired.",
            ],
        },
        "mashed-potato": {
            "title": "Mashed Potato",
            "macros": {"calories": 380, "protein": 8, "carbs": 55, "fats": 14},
            "ingredients": [
                "300g potatoes",
                "2 tbsp milk",
                "1 tbsp butter",
                "Salt, black pepper",
            ],
            "steps": [
                "Peel and cut potatoes.",
                "Boil until soft, then drain.",
                "Mash until smooth.",
                "Mix in butter and milk, season to taste.",
            ],
        },
    }

    if dish not in recipes_data:
        dish = "beef-bowl"

    return render_template("recipes.html", dish=dish, dish_data=recipes_data[dish])

# Timer
@app.get("/timer")
def timer():
    return render_template("timer.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
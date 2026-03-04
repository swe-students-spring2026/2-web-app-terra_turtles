## Project Requirement
See the [instructions](instructions.md) for more detail.


## Product vision statement

A data-driven gym and nutrition tracking web app that helps users achieve consistent strength and physique progress by making workouts and diet fully measurable and structured.


## Introduction to products
FitFlow is a lightweight gym and diet tracker designed to make progress measurable. The app helps users log workouts with clear, consistent data—exercise name, sets, reps, weight, and date—so they can actually see whether they are progressively overloading over time. Instead of relying on vague “it feels easier today,” users can look back at their history and make training decisions based on real numbers.

The workout side of FitFlow focuses on fast logging and easy review. Users can add new workout entries, search past lifts, edit mistakes, and delete outdated logs. A built-in rest timer supports training flow in the gym, so users can keep rest periods consistent and reduce guesswork during sessions.

FitFlow also includes a diet tracker for daily intake. Users can log meals with estimated calories and macronutrients (protein, carbs, fats), view daily totals, and set a target calorie goal to see how far they are above or below for the day. Together, the workout and diet features give users a simple way to track both training and nutrition in one place—without making the process slow or distracting.


# User stories

## Gym Tracking – Core Logging

As a gymgoer, I want to log exercises with sets, reps, and weight so that I can track my strength progression over time.

As a gymgoer, I want to record the date of each workout so that I can measure progress across weeks and months.

As a gymgoer, I want to be able to see my history of workouts so that I know whether I am progressively overloading. 

As a gymgoer, I want to be able to take notes on specific exercises that I did.  

As a gymgoer, I want to track total workout volume (sets × reps × weight) so that I can measure training intensity objectively.

As a gymgoer, I want a built-in rest timer so that I can keep rest periods consistent and measurable.

As a gymgoer, I want to quickly input reps and weight during rest so that logging does not interrupt my workout flow.

As a gymgoer, I want to compare performance across time periods so that I can evaluate whether my program is working.

As a gymgoer, I want to modify the added workout content so that I can conveniently correct any wrongly entered information.

As a gymgoer, I want to keep track of my weight changes so that I can adjust my training plan according to my weight.

## Diet Tracking

As a dieter, I want to log meals and estimated calories so that I can track my daily intake.

As a dieter, I want to know precisely how many calories I have consumed throughout the day so that I can plan my meals accordingly.

As a dieter, I want to track macronutrients (protein, carbs, fats) so that I can optimize for muscle gain or fat loss.

As a dieter, I want weekly calorie averages so that I can see trends rather than daily fluctuations. ( calculate average of daily calories of last 7 days)

As a dieter, I want to track body weight over time so that I can correlate diet with physical changes.

As a dieter, I want visual graphs of weight and calorie intake so that I can see whether my nutrition aligns with my goals.

As a dieter, I want to be able to modify my diet plan so that if the data I input is inaccurate, I can correct it and recalculate.

As a dieter, I want to have a cooking tutorial with descriptions to teach me how to prepare healthy food, so that I can know how to eat more healthily.

As a dieter, I want to have a BMI calculator so that I can assess whether my weight is excessive.

As a dieter, I want to have the option to input the calorie target for the current day, so that I can plan my three meals based on the difference.

# Steps necessary to run the software

## You may need to configure the .env file
```bash
# MongoDB (Atlas)
MONGO_URI="mongodb+srv://USERNAME:YOUR_PASSWORD@terraturtles.rufwskm.mongodb.net/?retryWrites=true&w=majority&appName=TerraTurtles"
MONGO_DBNAME="gym_info"

# Flask session key
SECRET_KEY="YOUR_PASSWORD"
```


## Mac / Linux

### 1) Clone the repo
```bash
git clone https://github.com/swe-students-spring2026/2-web-app-terra_turtles
cd 2-web-app-terra_turtles
```

### 2) Create .env
```bash
cp env.example .env
```
Then open the .env file and fill in the MONGO_URI and SECRET_KEY fields.

### 3) Install pipenv
```bash
pip install pipenv
```

### 4) Create and activate a virtual environment
```bash
pipenv shell
```

### 5) Install dependencies
```bash
pipenv install
```

### 6) Run the Flask app
```bash
pipenv run python3 app.py
```

### 7) Open in browser

Go to:
```
http://127.0.0.1:5000/
```


## Windows (PowerShell)
### 1) Clone the repo
```bash
git clone https://github.com/swe-students-spring2026/2-web-app-terra_turtles.git
cd 2-web-app-terra_turtles
```
### 2) Create .env
```bash
copy env.example .env
```
Then open the .env file and fill in the MONGO_URI and SECRET_KEY fields.

### 3) Install pipenv
```bash
pip install pipenv
```

### 4) Create and activate a virtual environment
```bash
pipenv shell
```

### 5) Install dependencies
```bash
pipenv install
```
### 6) Run the Flask app
```bash
pipenv run python app.py
```
### 7) Open in browser

Go to:
```
http://127.0.0.1:5000/
```


## Windows (Command Prompt / CMD)
### 1) Clone the repo
```bash
git clone https://github.com/swe-students-spring2026/2-web-app-terra_turtles.git
cd 2-web-app-terra_turtles
```

### 2) Create .env
```bash
copy env.example .env
```
Then open the .env file and fill in the MONGO_URI and SECRET_KEY fields.

### 3) Install pipenv
```bash
pip install pipenv
```

### 4) Create and activate a virtual environment
```bash
pipenv shell
```

### 5) Install dependencies
```bash
pipenv install
```

### 6) Run the Flask app
```bash
pipenv run python app.py
```

### 7) Open in browser

Go to:
```
http://127.0.0.1:5000/
```



## Task boards

[Project](https://github.com/orgs/swe-students-spring2026/projects)

## Project Requirement
See the [instructions](instructions.md) for more detail.


## Product vision statement

A data-driven gym and nutrition tracking web app that helps users achieve consistent strength and physique progress by making workouts and diet fully measurable and structured.


## Introduction to products
The app idea is to build a gym tracker so that people can monitor their progress at the gym and make sure they are progressively overloading so they can make consistent strength and hypertrophy progress. Without a tracker, they won’t be able to see the data and their progress explicitly, which may cause them to stick to the same weight for a long time (until they “feel” it is getting easier, which is vague and varies day by day), causing them to not make as much progress as they could have. 

After the user inputs their data, it can create charts and visualizations to show their progress. Maybe after a certain amount of datapoints, the software can even run a linear/non linear regression to predict their future gains based on their past data, if they stay consistent. 

But the core of the app is it tracks the date, and when the user hits the gym he inputs the exercise he is doing and the number of sets, reps, and weight of the exercise. 

There can also be a timer in the app to track resting time. The goal is to make everything measurable. 

Another idea is that the user can create their own workouts. For example, for back day they input the exercises they are going to do, and for each exercise they input the resting time and how many sets they want to do. Once they get to the gym, they can just boot up the app and the app will tell them how many sets they do and how long they rest between sets (with the timer). After each set, they can input the weight and reps for that set. This makes it so that most of the things are automated at the gym and the user doesn’t need to think a lot about it, and tracking is also easy because during rest time (which you can see with the timer) you just input the reps and weight (which is only 2 numbers, should take under 10 seconds). 

For each user there is also a diet component to the app. They can input what they ate and about how many calories the food is. The diet component can have similar features as the gym component. 


## User stories

### Gym Tracking – Core Logging

As a gymgoer, I want to log exercises with sets, reps, and weight so that I can track my strength progression over time.

As a gymgoer, I want to record the date of each workout automatically so that I can measure progress across weeks and months.

As a gymgoer, I want to see my previous performance for an exercise so that I know whether I am progressively overloading.

As a gymgoer, I want to view charts of my strength progression so that I can visually see improvement trends.

As a gymgoer, I want the app to detect when I have stagnated on an exercise so that I know when to increase weight or adjust volume.

As a gymgoer, I want predictions of future strength gains based on my past data so that I can set realistic goals.

As a gymgoer, I want to track total workout volume (sets × reps × weight) so that I can measure training intensity objectively.

### Gym Tracking – Workout Planning

As a gymgoer, I want to create custom workouts (e.g., Back Day, Push Day) so that I can follow a structured program.

As a gymgoer, I want to predefine the number of sets and rest time for each exercise so that my workout is automated and efficient.

As a gymgoer, I want the app to guide me through my workout step-by-step so that I don’t need to think about what comes next.

As a gymgoer, I want a built-in rest timer so that I can keep rest periods consistent and measurable.

As a gymgoer, I want the timer to automatically start after I log a set so that I don’t waste time between sets.

As a gymgoer, I want to quickly input reps and weight during rest so that logging does not interrupt my workout flow.

As a gymgoer, I want to repeat a previous workout template so that I can maintain consistency across weeks.

### Gym Tracking – Progress & Analytics

As a gymgoer, I want to see my estimated 1RM (one-rep max) based on logged sets so that I can track strength without testing maxes.

As a gymgoer, I want weekly and monthly summaries of workouts so that I can monitor consistency.

As a gymgoer, I want to compare performance across time periods so that I can evaluate whether my program is working.

As a gymgoer, I want reminders if I haven’t trained in several days so that I stay consistent.

### Diet Tracking

As a dieter, I want to log meals and estimated calories so that I can track my daily intake.

As a dieter, I want to see total daily calories automatically calculated so that I know if I am in a surplus or deficit.

As a dieter, I want to track macronutrients (protein, carbs, fats) so that I can optimize for muscle gain or fat loss.

As a dieter, I want weekly calorie averages so that I can see trends rather than daily fluctuations.

As a dieter, I want to track body weight over time so that I can correlate diet with physical changes.

As a dieter, I want visual graphs of weight and calorie intake so that I can see whether my nutrition aligns with my goals.

### Combined User Stories (Gym + Diet)

As a gymgoer and dieter, I want to see correlations between calorie intake and strength progress so that I understand how diet affects performance.

As a gymgoer and dieter, I want goal tracking (bulk, cut, maintenance) so that the app adjusts recommendations accordingly.

As a gymgoer and dieter, I want performance insights (e.g., strength plateau during calorie deficit) so that I can make informed adjustments.



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

http://127.0.0.1:5000/


## windows (PowerShell)
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

http://127.0.0.1:5000/


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

http://127.0.0.1:5000/



## Task boards

https://github.com/orgs/swe-students-spring2026/projects/18

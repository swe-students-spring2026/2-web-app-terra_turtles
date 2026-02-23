from itsdangerous import NoneAlgorithm
import pymongo
from bson.objectid import ObjectId
import datetime

import pymongo.server_api

user_id = input("Enter your mongodb user id: ")
password = input("Enter your mongodb password: ")

connection = pymongo.MongoClient("mongodb+srv://"+user_id+":"+password+"@terraturtles.rufwskm.mongodb.net/?appName=TerraTurtles")
db = connection["gym_info"]
sets = db["sets"]
meals = db["meals"]

#insert for sets database
def insertSets(user, email, exercise, weight, reps):
    #put in all user data
    doc = {
        "name":  user,
        "email": email,
        "weight":  weight,
        "exercise": exercise,
        "reps":  reps,
        "created_at": datetime.datetime.utcnow()
    }
    mongoid = sets.insert_one(doc)
    print(mongoid)

#insert for meal database
def insertMeals(user, email, meal, calories, protein):
    #put in all user data
    doc = {
        "name":  user,
        "email": email,
        "meal":  meal,
        "calories": calories,
        "protein":  protein,
        "created_at": datetime.datetime.utcnow()
    }
    mongoid = meals.insert_one(doc)
    print(mongoid)

#read for either database or both setFlag and mealFlag are true false for database we're using
def read(email, setFlag, mealFlag):
    # sorts docs by creation date
    if setFlag and mealFlag == False:
        return
    if setFlag == True:
        docs = sets.find({
            "email": email
        }).sort("created_at", -1)
        #parse info and print it out
        for doc in docs:
            output = '{name} ({user_email}) did {exercise} for {weight}lb for {reps} reps at {date}.'.format(
            name = doc["name"],
            user_email = doc["email"],
            exercise = doc["exercise"],
            weight = doc["weight"],
            reps = doc["reps"],
            date = doc["created_at"].strftime("%H:%M on %d %B %Y")
            )
            print(output)
    if mealFlag == True:
        docs = meals.find({
            "email": email
        }).sort("created_at", -1)
        #parse info and print it out
        for doc in docs:
            output = '{name} ({user_email}) ate {meal} ({calories} calories with {protein}g of protein) at {date}.'.format(
            name = doc["name"],
            user_email = doc["email"],
            meal = doc["meal"],
            calories = doc["calories"],
            protein = doc["protein"],
            date = doc["created_at"].strftime("%H:%M on %d %B %Y")
            )
            print(output)

#sets updateOne. If fields remain same, driver should set new_field to existing one by default
def updateOneSets(id, new_weight, new_reps, new_exercise):
    sets.update_one(
        #find id and put in new info
    { "_id": ObjectId(id) }, 
        {
        "$set": {
            "weight": new_weight,
            "reps": new_reps,
            "exercise": new_exercise,
            "created_at": datetime.datetime.utcnow()
            }
        }
    )

#updateOne meals
def updateOneMeal(id, new_meal, new_calories, new_protein):
    sets.update_one(
        #find id and put in new info
    { "_id": ObjectId(id) }, 
        {
        "$set": {
            "meal": new_meal,
            "calories": new_calories,
            "protein": new_protein,
            "created_at": datetime.datetime.utcnow()
            }
        }
    )

# was thinking of merging deleteOne and gets however for parameters sake (especially with gets), 
# it's easier to split up

#deletes first set file found from getID. 
def deleteOneSet(id):
    sets.delete_one({
    "_id": ObjectId(id)
})
    
#deletes first meal file found from getID. 
def deleteOneMeal(id):
    meals.delete_one({
    "_id": ObjectId(id)
})

#deletes all files fetched by getID. If set or meals should be excluded from delete, set to None
def deleteAll(setIDs, mealIDs):
    if setIDs is not None:
        for id in setIDs:
            sets.delete_many({
            "_id": ObjectId(id)
        })
    if mealIDs is not None:
        for id in mealIDs:
            meals.delete_many({
            "_id": ObjectId(id)
        })

#get only first id related to set fields. Fields excluded from search should be set to None
def getIDSets(name, email, exercise, weight, reps, created_at):
    params = locals()
    fields = {}
    #check which fields are None, and add to fields if not
    for field, val in params.items():
        if val is not None:
            fields[str(field)] = val
    # print(fields)
    docs = sets.find(fields)
    for doc in docs:
        return doc["_id"]

#get only first id related to meal fields. 
# Calories, protein, date should be a list with {$gte: min, $lte: max}
#for date, the min and max must be a datetime.datetime(year, month, day) (optional hour, minute, second parameters)

def getIDMeals(name, email, meal, calories, protein, date):
    params = locals()
    fields = {}
    #check which fields are None, and add to fields if not
    for field, val in params.items():
        if val is not None:
            fields[str(field)] = val
    # print(fields)
    docs = meals.find(fields)
    for doc in docs:
        return doc["_id"]

#get all IDS for sets following fields (instructions in getIDSet for parameters)
def getIDsSets(name, email, exercise, weight, reps, created_at):
    params = locals()
    fields = {}
    for field, val in params.items():
        if val is not None:
            fields[str(field)] = val
    docs = sets.find(fields)
    ids = []
    for doc in docs:
        ids.append(doc["_id"])
    return ids

#get all ids for meal database following parameters
def getIDsMeals(name, email, meal, calories, protein, date):
    params = locals()
    fields = {}
    for field, val in params.items():
        if val is not None:
            fields[str(field)] = val
    docs = meals.find(fields)
    ids = []
    for doc in docs:
        ids.append(doc["_id"])
    return ids








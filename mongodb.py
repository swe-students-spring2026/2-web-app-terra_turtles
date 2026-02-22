import pymongo
from bson.objectid import ObjectId
import datetime

import pymongo.server_api

user_id = input("Enter your mongodb user id: ")
password = input("Enter your mongodb password: ")

connection = pymongo.MongoClient("mongodb+srv://"+user_id+":"+password+"@sets.rufwskm.mongodb.net/?appName=TerraTurtles")
db = connection["Gym_info"]
col = db["sets"]

def insert(user, email, weight, reps):
    #put in all user data
    doc = {
        "name":  user,
        "email": email,
        "weight":  weight,
        "reps":  reps,
        "created_at": datetime.datetime.utcnow()
    }
    mongoid = col.insert_one(doc)
    print(mongoid)

def read(email):
    docs = col.find({
        "email": email
    })
    #parse info and print it out
    for doc in docs:
        output = '{name} ({user_email}) lifted {weight}lb for {reps} reps at {date}.'.format(
        name = doc["name"],
        user_email = doc["email"],
        weight = doc["weight"],
        reps = doc["reps"],
        date = doc["created_at"].strftime("%H:%M on %d %B %Y")
    )
    print(output)

def updateOne(id, new_weight, new_reps):
    col.update_one(
        #find id and put in new info
    { "_id": ObjectId(id) }, 
        {
        "$set": {
            "weight": new_weight,
            "reps": new_reps,
            "created_at": datetime.datetime.utcnow()
            }
        }
    )

#deletes first file found from email
def deleteOne(id):
    col.delete_one({
    "_id": ObjectId(id)
})

#deletes all files relateed to email 
def deleteAll(ids):
    for id in ids:
        col.delete_many({
        "_id": ObjectId(id)
    })
    
#get only first id related to email
def getID(email):
    docs = col.find({
        "email": email
    })
    for doc in docs:
        return doc["_id"]

#get all IDS
def getIDs(email):
    docs = col.find({
        "email": email
    })
    ids = []
    for doc in docs:
        ids.append(doc["_id"])
    return ids





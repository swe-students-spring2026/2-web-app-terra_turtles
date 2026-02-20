import pymongo
from bson.objectid import ObjectId
import datetime

user_id = input("Enter your mongodb user id: ")
password = input("Enter your mongodb password: ")

connection = pymongo.MongoClient("mongodb+srv://"+user_id+":"+password+"@terraturtles.rufwskm.mongodb.net/")
db = connection["TerraTurtles"]

def insert(user, email, weight, reps):
    doc = {
        "name":  user,
        "email": email,
        "weight":  weight,
        "reps":  reps,
        "created at": datetime.now(datetime.UTC)
    }
    mongoid = db.TerraTurtles.insert_one(doc)

def read(email):
    docs = db.TerraTurtles.find({
        "email": email
    })
    for doc in docs:
        output = '{name} ({user_email}) said "{message}" at {date}.'.format(
        name = doc.name,
        user_email = doc.email,
        date = doc.created_at.strftime("%H:%M on %d %B %Y") # nicely-formatted datetime
    )
    print(output)

def updateOne(id, new_weight, new_reps):
    db.collection_name.update_one( {
    { "_id": ObjectId(id) }, 
        {
        "$set": {
            "weight": new_weight,
            "reps": new_reps,
            "created_at": datetime.now(datetime.UTC)
        }
    }
    })

def deleteOne(id):
    db.TerraTurtles.delete_one({
    "_id": ObjectId(id)
})
    
def deleteMany(id):
    db.TerraTurtles.delete_many({
    "_id": ObjectId(id)
})

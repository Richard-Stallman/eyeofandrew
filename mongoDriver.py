from pymongo import MongoClient

def insert(data):
    # Replace dots with dashes in the keys
    mData = dict((k.replace(".","-"), v) for (k,v) in iter(data.items()))
    dbclient = MongoClient()
    db = dbclient["eyeofandrew"];
    collection = db["all"]
    collection.insert(mData)

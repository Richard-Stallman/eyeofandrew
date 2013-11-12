from pymongo import MongoClient
from datetime import datetime

def insert(data):
    mData = mongoFormat(data)
    dbclient = MongoClient()
    dbclient["eyeofandrew"]["all"].insert(mData)

def mongoFormat(data):
    results = []
    for host in data:
        for date in data[host]:
            for time in data[host][date]:
                for index in data[host][date][time]:
                    dt = datetime.strptime("{} {}".format(date, time), "%m/%d/%y %H:%M:%S")
                    e = data[host][date][time][index]
                    keys = {"host": host,
                            "time": dt,
                            "user": e["user"],
                            "prog": e["prog"],
                            "cpu": e["jcpu"],
                            "tty": e["tty"],
                            "from": e["from"],
                            "login": e["login"],
                            "idle": e["idle"]
                           }
                    results.append(keys)
    return results

class Query:
    def __init__(self):
        self.db = MongoClient()["eyeofandrew"]["all"]

    def execute(self, *details):
        queries = [getattr(self, name)(value) for (name, value) in details]
        query = {k:v for q in queries for k,v in q.items()}
        return self.db.find(query)

    def machine(self, name):
        return {"host": name}

    def timeBetween(self, timeT):
        (start, end) = timeT
        return {"time": {"$gte": start, "$lt": end}}

    def user(self, andrewid):
        return {"user": andrewid}

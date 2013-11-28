from pymongo import MongoClient
from datetime import datetime, timedelta

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
        self.query = ""

    def build(self, data):
        QD = QueryData()
        queries = [getattr(QD, name)(value) for (name, value) in data.items()]
        query = {k:v for q in queries for k,v in q.items()}
        self.query = query

    def execute(self, restrict=None):
        if restrict is None:
            return self.db.find(self.query, {"_id": 0})
        return self.db.find(self.query, {restrict: 1, "_id": 0})

    def find(self, sort="time"):
        return self.execute().sort(sort)

    def count(self):
        return self.execute().count()

class QueryData:
    # Takes prefix of the desired computer
    def host(self, name):
        return {"host": name}

    # Returns events within close proximity to the given time
    def time(self, time):
        d = timedelta(seconds=5)
        return {"time": {"$lt": time + d, "$gte": time - d}}

    def user(self, andrewid):
        return {"user": andrewid}

    def prog(self, prog):
        return {"prog": prog}

class SlowData:
    def __init__(self):
        self.db = MongoClient()["eyeofandrew"]["all"]

    # Return a list of unique collection events
    def queryTimes(self):
        times = self.db.find(None, {"time":1}).distinct("time")
        timeSet = {t.replace(second=(t.second % 5)) for t in times}
        return sorted(timeSet)

    # Return a list of unique machine names
    def machines(self):
        return self.db.find(None, {"host":1}).distinct("host")

class Visualization:
    def __init__(self):
        SD = SlowData()
        self.queryTimes = SD.queryTimes()
        self.machines = SD.machines()
        self.query = Query()
        self.countedHosts = self.hostCount()

    def hostCount(self):
        result = dict()
        for time in self.queryTimes:
            self.query.build({"time":time})
            qResult = self.query.execute("host")
            counter = dict()
            for row in qResult:
                host = row["host"]
                counter[host] = (counter[host] + 1 if host in counter else 1)
            result[time] = counter
        return result

    def hostData(self, host):
        return dict((k, v[host]) if host in v else (k,0) for k,v in self.countedHosts.items())

from pymongo import MongoClient
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('SVG')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from mpl_toolkits.mplot3d.axes3d import Axes3D
from pprint import pprint

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

    # Return a list of unique program names
    def programs(self):
        return self.db.find(None, {"prog":1}).distinct("prog")


class Visualization:
    def __init__(self):
        self.queryTimes = None
        self.machines = None
        self.programs = None
        self.query = Query()
        self.countedHosts = None
        self.countedPrograms = None

    def hostCount(self):
        if self.queryTimes is None:
            self.queryTimes = SlowData().queryTimes()
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

    def programCount(self):
        if self.programs is None:
            self.programs = SlowData().programs()
        counter = dict()
        for prog in self.programs:
            self.query.build({"prog": prog})
            counter[prog] = self.query.count()
        return counter

    def hostCountOutput(self, host):
        if self.countedHosts is None:
            self.countedHosts = self.hostCount()
        print("Drawing graph for {}".format(host))
        result = dict((k, v[host]) if host in v else (k,0) for k,v in self.countedHosts.items())
        fig = plt.gcf()
        fig.set_size_inches(200,10)
        plt.ion()
        plt.plot([k for k,_ in result.items()], [v for _,v in result.items()], "ro")
        formatter = DateFormatter('%H:%M %b %d')
        plt.gca().xaxis.set_major_locator(matplotlib.dates.HourLocator())
        plt.gcf().axes[0].xaxis.set_major_formatter(formatter)
        plt.gcf().autofmt_xdate()
        plt.title("Simultaneous users of {} over time".format(host))
        plt.xlabel("Time")
        plt.ylabel("Number of Users")
        plt.grid(True)
        plt.savefig("users/{}".format(host.split(".")[0]), bbox_inches="tight")
        plt.clf()

    def hostCountVisualize(self):
        if self.machines is None:
            self.machines = SlowData().machines()
        for machine in self.machines:
            self.hostCountOutput(machine)

    def programCountVisualize(self):
        if self.countedPrograms is None:
            self.countedPrograms = self.programCount()
        fig = plt.gcf()
        fig.set_size_inches(200, 200)
        plt.ion()
        progData = sorted(self.countedPrograms.items(), key=lambda x: x[1], reverse=True)
        progData = progData[:40]
        labels = [x for (x,_) in progData]
        counts = [x for (_,x) in progData]
        plt.pie(counts, labels=labels, autopct=lambda p: '{:.2f}%'.format(p), pctdistance=.9)
        plt.title("Most popular programs run on the CMU servers")
        plt.savefig("prog/count", bbox_inches="tight")
        plt.clf()

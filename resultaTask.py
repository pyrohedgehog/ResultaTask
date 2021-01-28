from datetime import datetime, timedelta
import requests
from os import environ
# lets have a singleton to call the

# so, lets take this api call data, strip it down to what we need in a python class, reconvert that to json, and return that!

class APISingleton():
    # Using a singleton because you can add more for optimization features under the hood
    # eg, you may be able to cache the team rankings (I will not be doing so in this exercise)
    __instance = None

    # @@@@@@@@@CHECK THIS! WILL NOT RUN WITHOUT THIS SET@@@@@@@@@
    api_key = environ.get("RESULTA_API_KEY")

    baseURL = "https://delivery.chalk247.com/"
    urlOptions = {"scoreBoard": "scoreboard/",
                  "teamRanking": "team_rankings/"
                  }
    dateTimeFormat = "%Y-%m-%d"

    @staticmethod
    def getInstance():
        if (APISingleton.__instance == None):
            APISingleton()

        return APISingleton.__instance

    def __init__(self):
        if APISingleton.__instance != None:
            raise Exception("I made this a singleton to save room for future improvement")
        else:
            APISingleton.__instance = self

    def _getTeamRanksAsClasses(self, league='NFL'):
        ranks = requests.get(
            "{}{}{}.json?api_key={}".format(self.baseURL, self.urlOptions['teamRanking'], league, self.api_key)).json()
        ans = []
        ranks = ranks['results']['data']
        for x in ranks:
            ans.append(_rank(x))

        return ans

    def isOutsideTimeWindow(self, startDate, endDate):
        # check if they are over 7 days apart
        d1, d2 = self._getDatesAsObjects(startDate, endDate)
        return d1 + timedelta(days=7) < d2

    def _handleOutsideAllowedTime(self, startDate, endDate, league="NFL"):
        ONE_DAY = timedelta(days=1)
        # I did one day pagination. There are better ways that reduce network latency, but that's a little overkill for this.
        d1, _ = self._getDatesAsObjects(startDate, endDate)
        d2 = d1 + ONE_DAY
        date1 = startDate
        date2 = self._turnDateObjToString(d2)
        ans = []
        while (date2 <= endDate):
            foo = self._queryForSolutionAsDict(date1, date2, league=league)

            # add those answers into the list
            for x in foo:
                ans.append(x)

            # iterate forward one day
            d1 += ONE_DAY
            d2 += ONE_DAY
            date1 = self._turnDateObjToString(d1)
            date2 = self._turnDateObjToString(d2)
        return ans

    def _queryForSolutionAsDict(self, startDate, endDate, league='NFL'):
        foo = "{}{}{}/{}/{}.json?api_key={}".format(self.baseURL, self.urlOptions['scoreBoard'], league, startDate,
                                                    endDate, self.api_key)
        scores = requests.get(foo).json()
        # we're not going to be checking the hash ATM, but that would be inserted here as a future step.
        scores = scores['results']

        ranks = self._getTeamRanksAsClasses(league=league)

        ans = []
        for x in scores:
            foo = scores[x]
            if (foo != []):
                foo = foo['data']
                #  edge case of empty date
                for y in foo:
                    ans.append(_eventMerger(ranks, foo[y]).getDict())
        return ans

    def getSolution(self, startDate, endDate, league='NFL'):
        startDate, endDate = self._smallerDateFirst(startDate, endDate)

        if (self.isOutsideTimeWindow(startDate, endDate)):
            return self._handleOutsideAllowedTime(startDate, endDate, league=league)
        else:
            return self._queryForSolutionAsDict(startDate, endDate, league=league)

    def _smallerDateFirst(self, startDate, endDate):
        d1, d2 = self._getDatesAsObjects(startDate, endDate)

        if (d1 > d2):
            return endDate, startDate
        else:
            return startDate, endDate

    def _getDatesAsObjects(self, d1, d2):
        d1 = datetime.strptime(d1, self.dateTimeFormat)
        d2 = datetime.strptime(d2, self.dateTimeFormat)
        return d1, d2

    def _turnDateObjToString(self, d):
        return d.strftime(self.dateTimeFormat)


class _rank():
    # this is purely for sanity sake. I would much rather work with a class than a json dict.
    # there are cleaner ways to do this with libraries (eg, the json library has support to make a class, but this way
    # there is more clarity and autofill ide support.)
    def __init__(self, str):
        self.team_id = str['team_id']
        self.team = str['team']
        self.rank = str['rank']
        self.last_week = str['last_week']
        self.points = round(float(str["points"]), 2)  # the specifications say to round to 2 points.
        self.modifier = str['modifier']
        self.adjusted_points = str['adjusted_points']

    def __repr__(self):
        ans = """'team_id': '{}', 'team': '{}', 'rank': '{}', 'last_week': '{}', 'points': '{}', 'modifier': '{}', 'adjusted_points': '{}'"""
        return ans.format(self.team_id, self.team, self.rank, self.last_week, self.points, self.modifier,
                          self.adjusted_points)


class _eventMerger():
    # my purpose in life is to take in the two json arrays and convert it into one json object(do this in series to create the array)
    #
    # a demo format, (would be removed, but I am hoping this can clearly show my train of thought)
    # {
    #     "event_id": "1233827",
    #     "event_date": "12-01-2020",
    #     "event_time": "15:05",
    #     "away_team_id": "42",
    #     "away_nick_name": "Texans",
    #     "away_city": "Houston",
    #     "away_rank": "21",
    #     "away_rank_points": "-6.00",
    #     "home_team_id": "63",
    #     "home_nick_name": "Chiefs",
    #     "home_city": "Kansas City",
    #     "home_rank": "2",
    #     "home_rank_points": "21.20"
    # }
    def __init__(self, ranks, event):
        self.event_id = event["event_id"]
        self.event_date = event['event_date'][:-6]
        self.event_time = event['event_date'][-5:]

        self.away_team_id = event['away_team_id']
        self.away_nick_name = event['away_nick_name']
        self.away_city = event['away_city']
        self.away_rank = -1
        self.away_rank_points = -1

        self.home_team_id = event['home_team_id']
        self.home_nick_name = event['home_nick_name']
        self.home_city = event['home_city']
        self.home_rank = -1
        self.home_rank_points = -1

        # here ranks are handled
        aFound = False  # technically more efficient, but not really needed.
        hFound = False
        for x in ranks:
            if (x.team_id == self.away_team_id):
                self.away_rank = str(x.rank)
                self.away_rank_points = str(x.points)
                aFound = True
            # in case the team faces itself somehow, these are separate points
            if (x.team_id == self.home_team_id):
                self.home_rank = str(x.rank)
                self.home_rank_points = str(x.points)
                hFound = True
            if (aFound and hFound):
                return

    def getDict(self):
        return self.__dict__

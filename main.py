from datetime import datetime, timezone
from os import environ
from urllib.request import urlretrieve
from os.path import abspath, dirname, join, isfile

class dataDate():
    def __init__(self):
        self.now = datetime.now(timezone.utc)
        self.year = self.now.year
        self.day = self.now.strftime("%d")
        self.month = self.now.strftime("%m")
        self.monthAbbrv = self.now.strftime("%b")

class data():
    def __init__(self):
        self.date = dataDate()
        self.dir = directory(self.date)
        self.address = F'https://noaadata.apps.nsidc.org/NOAA/G02158/unmasked/{self.date.year}/{self.date.month}_{self.date.monthAbbrv}/SNODAS_unmasked_{self.date.year}{self.date.month}{self.date.day}.tar'
    def download(self):
        if not isfile(self.dir.downloadLocation):  #might remove for production
            environ["no_proxy"] = "*"
            print(urlretrieve(self.address, self.dir.downloadLocation))
        else:
            print('file already downloaded; proceeding')
    def unzip(self):
        pass

class directory():
    def __init__(self, date):
        self.workingDirectory = dirname(abspath(__file__))
        self.name = F'SNODAS-{date.year}{date.month}{date.day}.tar'
        self.downloadLocation = join(self.workingDirectory, 'data', self.name)
todaysData = data()
todaysData.download()

def check4file(path):
    pass
def waitForDL():
    #wait for file download to finish and then run processing tasks
    #if checkFile true run processing
    return

def checkFile():
    #check a folder for a file
    return

def unzip():
    return

def makeHeader():
    #make a header for a snodas file as
    return

def createCOG():
    return

def removeTmp():
    return
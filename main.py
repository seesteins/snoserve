from datetime import datetime, timezone
from os import environ, chdir, listdir, path, remove
from urllib.request import urlretrieve
from os.path import abspath, dirname, join, isfile
from shutil import unpack_archive, copyfileobj
import gzip

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
        if not isfile(self.dir.download):  #might remove for production
            environ["no_proxy"] = "*"
            print(urlretrieve(self.address, self.dir.download))
        else:
            print('file already downloaded; proceeding')
    def extractTAR(self):
        unpack_archive(self.dir.download, self.dir.extract)
        return self.dir.extract
    def extractGZ(self):
        extension = '.gz'
        chdir(self.dir.extract)
        for item in listdir(self.dir.extract):
            if item.endswith(extension):
                nameGZ = path.abspath(item)
                outputName = (path.basename(nameGZ)).rsplit('.',1)[0]
                with gzip.open(nameGZ, 'rb') as fileIn, open(outputName, 'wb') as fileOut:
                    copyfileobj(fileIn, fileOut)
                remove(nameGZ)
        chdir(self.dir.workingDirectory)

class directory():
    def __init__(self, date):
        self.workingDirectory = dirname(abspath(__file__))
        self.name = F'SNODAS-{date.year}{date.month}{date.day}'
        self.download = join(self.workingDirectory, 'data', self.name + '.tar')
        self.extract = join(self.workingDirectory, 'data', self.name)
todaysData = data()
todaysData.download()
todaysData.extractTAR()
todaysData.extractGZ()

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
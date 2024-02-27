import gzip
from datetime import datetime, timezone
from os import chdir, environ, listdir, path, remove
from os.path import abspath, dirname, isfile, join
from shutil import copyfileobj, unpack_archive
from urllib.request import urlretrieve

from osgeo.gdal import Translate


class dataDate:  # a class to get the time for data download and naming purposes
    def __init__(self):
        self.now = datetime.now(timezone.utc)
        self.year = self.now.year
        self.day = self.now.strftime("%d")
        self.month = self.now.strftime("%m")
        self.monthAbbrv = self.now.strftime("%b")


class data:
    def __init__(self):
        self.date = dataDate()
        self.dir = directory(self.date)
        self.address = f"https://noaadata.apps.nsidc.org/NOAA/G02158/unmasked/{self.date.year}/{self.date.month}_{self.date.monthAbbrv}/SNODAS_unmasked_{self.date.year}{self.date.month}{self.date.day}.tar"

    def download(self):
        # downloads current SNODAS data if not previously downloaded today
        if not isfile(self.dir.download):  # might remove for production
            environ["no_proxy"] = "*"
            print(urlretrieve(self.address, self.dir.download))
        else:
            print("file already downloaded; proceeding")

    def extractTAR(self):
        unpack_archive(self.dir.download, self.dir.extract)
        return self.dir.extract

    def extractGZ(self):
        # extracts all .gz files in a folder and removes the original archives
        extension = ".gz"
        chdir(self.dir.extract)
        for item in listdir(self.dir.extract):
            if item.endswith(extension):
                nameGZ = path.abspath(item)
                outputName = (path.basename(nameGZ)).rsplit(".", 1)[0]
                with gzip.open(nameGZ, "rb") as fileIn, open(
                    outputName, "wb"
                ) as fileOut:
                    copyfileobj(fileIn, fileOut)
                remove(nameGZ)
        chdir(self.dir.workingDirectory)

    def createTiffs(self):
        pass


class GTIFF:
    def __init__(self, txt, dat, hdr):
        self.txt = txt  # set .txt file path
        self.dat = dat  # set .dat file path
        self.hdr = hdr

    def readTxt(self):
        # reads the snodas .txt files and saves the values to a dictionary
        self.metadata = {}
        with open(self.txt) as metafile:
            for var in metafile:
                (key, val) = var.rstrip().split(": ")
                self.metadata[key] = val
        return self.metadata

    def stringHDR(self):
        # creates the text of the .hdr file - might be able to use this without an
        # an additional file operation
        samples = self.metadata["Number of columns"]
        lines = self.metadata["Number of rows"]
        self.envi = [
            "ENVI",
            f"samples = {samples}",
            f"lines = {lines}",
            "bands = 1",
            "header offset = 0",
            "file type = ENVI Standard",
            "data type = 2",
            "interleave = bsq",
            "byte order = 1",
        ]
        self.envi = "\n".join(self.envi)
        return self.envi

    def createHDR(self):
        self.stringHDR()
        with open(self.hdr, "w") as hdr:
            hdr.write(self.envi)
        return self.hdr

    def process(self, dest):
        minX = float(self.metadata["Minimum x-axis coordinate"])
        minY = float(self.metadata["Minimum y-axis coordinate"])
        maxX = float(self.metadata["Maximum x-axis coordinate"])
        maxY = float(self.metadata["Maximum y-axis coordinate"])
        a_ullr = [minX, maxY, maxX, minY]
        kwargs = {
            "format": "Gtiff",
            "outputSRS": "epsg:4326",
            "noData": float(self.metadata["No data value"]),
            "outputBounds": a_ullr,
        }
        Translate(dest, self.dat, **kwargs)

    def depthStyle(self):
        pass

    def sweStyle(self):
        pass


class directory:
    def __init__(self, date):
        self.workingDirectory = dirname(abspath(__file__))
        self.date = f"{date.year}{date.month}{date.day}"
        self.name = f"SNODAS-{self.date}"
        self.data = join(self.workingDirectory, "data")
        self.tmp = join(self.data, "tmp")
        self.download = join(self.tmp, self.name + ".tar")
        self.extract = join(self.tmp, self.name)
        self.finalData = join(self.data, self.name)
        self.swe = join(self.finalData, f"swe{self.date}.tif")
        self.snowDepth = join(self.finalData, f"snowdepth{self.date}.tif")

    def unzippedName(self, extension, zippedFile):  # refactor extract GZ in future
        pass


txt = "/home/tetonicus/programming/SNOServe/data/SNODAS-20240226/zz_ssmv01025SlL00T0024TTNATS2024022605DP001.txt"
dat = "/home/tetonicus/programming/SNOServe/data/SNODAS-20240226/zz_ssmv01025SlL00T0024TTNATS2024022605DP001.dat"
hdr = "/home/tetonicus/programming/SNOServe/data/SNODAS-20240226/zz_ssmv01025SlL00T0024TTNATS2024022605DP001.hdr"
dest = "/home/tetonicus/programming/SNOServe/data/SNODAS-20240226/zz_ssmv01025SlL00T0024TTNATS2024022605DP001.tif"
someData = GTIFF(txt, dat, hdr)
someData.readTxt()
someData.createHDR()
someData.process(dest)


def createCOG():
    return


def removeTmp():
    return

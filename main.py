import gzip
import pathlib
from datetime import datetime, timedelta, timezone
from os import chdir, environ, listdir, path, remove
from os.path import abspath, dirname, isfile, join
from shutil import copyfileobj, unpack_archive
from subprocess import check_call
from urllib.request import urlretrieve

from osgeo.gdal import Translate


class dataDate:  # a class to get the time for data download and naming purposes
    def __init__(self):
        tz = timezone("US/Eastern")
        now = datetime.now(tz)
        releaseTime = now.replace(hour=9, minute=15, second=0, microsecond=0)
        if now < releaseTime:
            self.latestData = now - timedelta(days=1)
        else:
            self.latestData = now
        self.year = self.latestData.strftime("%Y")
        self.day = self.latestData.strftime("%d")
        self.month = self.latestData.strftime("%m")
        self.monthAbbrv = self.latestData.strftime("%b")


class data:
    def __init__(self, date):
        self.date = date
        self.dir = directory(self.date)
        self.dir.create()
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

    def createTiffs(self, colorize=False):
        filenames = self.dir.finalNames
        for item in listdir(self.dir.extract):
            if item.endswith(".txt"):
                tiff = GTIFF(stripExtension(item), self.dir)
                tiff.createHDR()
                tiff.process(self.dir, filenames[tiff.metadata["Description"]])
                if colorize:
                    self.colorize(tiff)

    def colorize(self, tiff):
        # test if input file has a colortable file
        if tiff.name in [
            stripExtension(file) for file in listdir(self.dir.colortables)
        ]:
            tiff.colorize(self.dir)


class GTIFF:
    def __init__(self, filename, directory):
        # pass in a dat fill
        self.txt = join(directory.extract, f"{filename}.txt")  # set .txt file path
        self.dat = join(directory.extract, f"{filename}.dat")  # set .dat file path
        self.hdr = join(directory.extract, f"{filename}.hdr")
        self.metadata = readTXTvars(self.txt)

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

    def process(self, dir, filename):
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
        dest = join(dir.finalData, f"{filename}.tif")
        Translate(dest, self.dat, **kwargs)
        self.fullPath = dest
        self.name = filename

    def colorize(self, dir, colortxt=None, output_file=None):
        # need to call a command in the shell for this to work
        if output_file is None:
            output_file = self.fullPath
        if colortxt is None:
            colortxt = join(dir.colortables, f"{self.name}.txt")
        cmd = f"gdaldem color-relief {self.fullPath} {colortxt} {output_file} -alpha"
        check_call(cmd, shell=True)

    def convertToInches(self):
        pass

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
        self.tmp = join(self.workingDirectory, "tmp")
        self.download = join(self.tmp, self.name + ".tar")
        self.extract = join(self.tmp, self.name)
        self.finalData = join(self.data, self.name)
        self.swe = join(self.finalData, f"swe{self.date}.tif")
        self.snowDepth = join(self.finalData, f"snowdepth{self.date}.tif")
        self.colortables = join(self.workingDirectory, "colortables")
        self.folders = [
            self.data,
            self.tmp,
            self.finalData,
            self.extract,
            self.colortables,
        ]
        self.filenames = join(self.workingDirectory, "filenames.txt")
        self.finalNames = readTXTvars(self.filenames)

    def create(self):
        # creates folders for data
        for folder in self.folders:
            pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

    def outputDirs(self):
        # takes the filenames.txt file and creates a dictionary with the locations to
        # to save processed data
        self.finalNames = readTXTvars(self.filenames)
        self.outputPaths = {}
        for key in self.finalNames:
            self.outputPaths[key] = join(self.finalData, f"{self.finalNames[key]}.tif")
        return self.outputPaths

    def unzippedName(self, extension, zippedFile):  # refactor extract GZ in future
        pass


def readTXTvars(txt):
    variables = {}
    with open(txt) as varfile:
        for var in varfile:
            (key, val) = var.rstrip().split(": ")
            variables[key] = val
    return variables


def stripExtension(file):
    return (path.basename(file)).rsplit(".", 1)[0]


date = dataDate()
currentData = data(date)
currentData.download()
currentData.extractTAR()
currentData.extractGZ()
currentData.createTiffs(True)

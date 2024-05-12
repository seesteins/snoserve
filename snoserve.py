from datetime import datetime, timedelta
from gzip import open as gunzip
from os import chdir, environ, getenv, listdir, path, remove, system
from os.path import abspath, dirname, isfile, join
from pathlib import Path
from shutil import copyfileobj, rmtree, unpack_archive
from subprocess import check_call
from urllib.request import urlretrieve

from dotenv import load_dotenv
from geoserver.catalog import Catalog
from osgeo.gdal import Translate, TranslateOptions
from pytz import timezone


class dataDate:  # a class to get the time for data download and naming purposes
    def __init__(self):
        tz = timezone("US/Eastern")
        now = datetime.now(tz)
        releaseTime = now.replace(hour=9, minute=15, second=0, microsecond=0)
        if now < releaseTime:
            self.latest_data = now - timedelta(days=1)
        else:
            self.latest_data = now
        self.year = self.latest_data.strftime("%Y")
        self.day = self.latest_data.strftime("%d")
        self.month = self.latest_data.strftime("%m")
        self.date_string = f"{self.year}{self.month}{self.day}"
        self.monthAbbrv = self.latest_data.strftime("%b")


class file:  # download data and drives the extraction and processing
    def __init__(self, date):
        self.date = date
        self.dir = directory(self.date)
        self.dir.create()
        self.address = f"https://noaadata.apps.nsidc.org/NOAA/G02158/unmasked/{self.date.year}/{self.date.month}_{self.date.monthAbbrv}/SNODAS_unmasked_{self.date.year}{self.date.month}{self.date.day}.tar"

    def download(self):  # downloads current SNODAS data if not existing
        if not isfile(self.dir.download):  # might remove for production
            environ["no_proxy"] = "*"
            print(urlretrieve(self.address, self.dir.download))
        else:
            print("file already downloaded; proceeding")

    def extractTAR(self):  # extract download tar file
        unpack_archive(self.dir.download, self.dir.extract)
        return self.dir.extract

    def extractGZ(self):  # extract all .gz files from .tar extraction rm originals
        extension = ".gz"
        chdir(self.dir.extract)
        for item in listdir(self.dir.extract):
            if item.endswith(extension):
                nameGZ = path.abspath(item)
                outputName = (path.basename(nameGZ)).rsplit(".", 1)[0]
                with gunzip(nameGZ, "rb") as fileIn, open(outputName, "wb") as fileOut:
                    copyfileobj(fileIn, fileOut)
                remove(nameGZ)
        chdir(self.dir.workingDirectory)

    def createTiffs(self, colorize=False):
        """
        Creates GeoTIFF files from the extracted .txt and .dat files.

        Args:
            colorize (bool, optional): If True, applies color relief to the generated GeoTIFF files using the corresponding color table files. Defaults to False.

        This method iterates through the extracted files in the `self.dir.extract` directory.
        For each file with a `.txt` extension, it performs the following steps:

        1. Creates a `GTIFF` object with the file name and directory object.
        2. Generates a `.hdr` file for the GeoTIFF using the `GTIFF.createHDR()` method.
        3. Retrieves the output file name from the `self.dir.finalNames` dictionary based on the 'Description' metadata.
        4. Processes the `.dat` file and generates a GeoTIFF file in the `self.dir.finalData` directory using the `GTIFF.process()` method.
        5. If `colorize` is True, applies color relief to the generated GeoTIFF file using the `self.colorize()` method.
        """
        filenames = self.dir.finalNames
        for item in listdir(self.dir.extract):
            if item.endswith(".txt"):
                tiff = GTIFF(strip_extension(item), self.dir)
                tiff.createHDR()
                filename = filenames[tiff.metadata["Description"]]
                tiff.process(self.dir, filename)
                if colorize:
                    self.colorize(tiff)

    def colorize(self, tiff):  # colors GTIFF if 'name'.txt is provided in colortables
        if tiff.name in [
            strip_extension(file) for file in listdir(self.dir.colortables)
        ]:
            tiff.colorize(self.dir)

    def cleantemp(self):  # removes extracted files
        # currently leaves .tar file to prevent DDOSing NOAA
        rmtree(self.dir.extract)

    def clean_old_tar(self):
        pass

    def clean_old_data(self):
        pass


class GTIFF:  # processes individual geotiff files
    def __init__(self, filename, directory):
        # pass in a filename and directory object
        self.txt = join(directory.extract, f"{filename}.txt")  # set .txt file path
        self.dat = join(directory.extract, f"{filename}.dat")  # set .dat file path
        self.hdr = join(directory.extract, f"{filename}.hdr")
        self.metadata = read_txt_vars(self.txt)

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
        noData = float(self.metadata["No data value"])
        options = TranslateOptions(
            format="Gtiff",
            outputSRS="epsg:4326",
            noData=noData,
            outputBounds=a_ullr,
            metadataOptions=self.metadata,
        )
        dest = join(dir.finalData, f"{filename}.tif")
        Translate(dest, self.dat, options=options)
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
        pass  # future work


class directory:  # directory manager
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
        self.finalNames = read_txt_vars(self.filenames)
        self.environment = join(self.workingDirectory, ".env")

    def create(self):
        # creates folders for data
        for folder in self.folders:
            Path(folder).mkdir(parents=True, exist_ok=True)

    def outputDirs(self):
        # takes the filenames.txt file and creates a dictionary with the locations to
        # to save processed data
        self.finalNames = read_txt_vars(self.filenames)
        self.outputPaths = {}
        for key in self.finalNames:
            self.outputPaths[key] = join(self.finalData, f"{self.finalNames[key]}.tif")
        return self.outputPaths

    def unzippedName(self, extension, zippedFile):  # refactor extract GZ in future
        pass


class server:
    def __init__(self):
        load_dotenv()
        self.HOST = getenv("GEOSERVER_ADDRESS")
        self.USERNAME = getenv("GEOSERVER_USERNAME")
        self.PASSWORD = getenv("GEOSERVER_PASS")
        self.geoserver = Catalog(self.HOST, self.USERNAME, self.PASSWORD)
        self.geoserver

    def upload_data(self, data_name, workspace, local_path):
        return self.geoserver.create_coveragestore(
            data_name,
            workspace=workspace,
            path=local_path,
            upload_data=True,
            overwrite=True,
        )

    def style_data(self, layer_name, style_name):
        layer = self.geoserver.get_layer(layer_name)
        style = f"<layer><defaultStyle><name>{style_name}</name></defaultStyle></layer>"
        cmd = f'curl -u {self.USERNAME}:{self.PASSWORD} -XPUT -H "Content-type: text/xml" -d "{style}" {self.HOST}/layers/SNODAS:{layer.name}'
        system(cmd)

    def upload_folder(self, workspace, folder_path):
        for data in listdir(folder_path):
            if data.endswith(".tif"):
                data_path = join(folder_path, data)
                name = (path.basename(data)).rsplit(".", 1)[0]
                self.upload_data(name, workspace, data_path)

    def delete_data(self, data_name, workspace):
        store = self.geoserver.get_store(name=data_name, workspace=workspace)
        return self.geoserver.delete(store, purge=True, recurse=True)

    def upload_style(self, style):
        with open(style) as file:
            self.geoserver.create_style(
                strip_extension(path.basename(style)), file.read()
            )

    def delete_old_data(self, date, days):
        # no longer following this naming convention
        stores = self.get_all_data()
        for store in stores:
            if store["date"] < date.latest_data - timedelta(days):
                self.geoserver.delete(store["obj"], purge=True, recurse=True)

    def get_all_data_dates(self):
        # no longer using this data format
        all_stores = self.geoserver.get_stores()
        stores = []
        for store in all_stores:
            stores.append(
                {
                    "name": store.name,
                    "date": datetime_from_str(store.name.split("_")[-1]),
                    "obj": store,
                }
            )
        return stores

    def style_types(self, types_list):
        stores = self.geoserver.get_stores()
        for store in stores:
            data_type = store.name
            if data_type in types_list:
                self.style_data(store.name, data_type)

    def selective_upload(self, workspace, folder_path, selection):
        selection = [f"{file}.tif" for file in selection]
        for file in listdir(folder_path):
            if file in selection:
                data_path = join(folder_path, file)
                name = (path.basename(file)).rsplit(".", 1)[0]
                self.upload_data(name, workspace, data_path)


def read_txt_vars(txt):  # reads .txt into a dictionary "key: value\n"
    variables = {}
    with open(txt) as varfile:
        for var in varfile:
            (key, val) = var.rstrip().split(": ")
            variables[key] = val
    return variables


def strip_extension(file):  # strips the first extension from a file
    return (path.basename(file)).rsplit(".", 1)[0]


def datetime_from_str(string):
    tz = timezone("US/Eastern")
    date = datetime.strptime(string, "%Y%m%d").replace(tzinfo=tz)
    return date


def main():
    date = dataDate()
    current_data = file(date)
    current_data.download()
    current_data.extractTAR()
    current_data.extractGZ()
    current_data.createTiffs()
    current_data.cleantemp()
    verty = server()
    verty.selective_upload("SNODAS", current_data.dir.finalData, ["snowdepth", "swe"])
    verty.style_types(["snowdepth", "swe"])


if __name__ == "__main__":
    main()

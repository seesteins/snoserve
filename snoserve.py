from datetime import datetime, timedelta
from gzip import open as gunzip
from os import chdir, environ, getenv, listdir, path, remove, system
from os.path import abspath, dirname, isfile, join
from pathlib import Path
from shutil import copyfileobj, rmtree, unpack_archive
from subprocess import check_call
from urllib.request import urlretrieve

from geoserver.catalog import Catalog
from osgeo.gdal import Translate, TranslateOptions
from pytz import timezone


class dataDate:
    """
    A class to determine the appropriate date for data download and naming purposes.

    This class determines the latest date for which SNODAS data should be downloaded and processed.
    It accounts for the release time of the data, which is typically at 9:15 AM Eastern Time.
    If the current time is before the release time, the class will use the date from the previous day.

    Attributes:
        latest_data (datetime.datetime): The latest date for which SNODAS data should be downloaded and processed.
        year (str): The year component of latest_data in YYYY format.
        day (str): The day component of latest_data in DD format.
        month (str): The month component of latest_data in MM format.
        date_string (str): The date string in YYYYMMDD format.
        monthAbbrv (str): The abbreviated month name (e.g., Jan, Feb, Mar) corresponding to latest_data.

    Example:
        >>> date_obj = dataDate()
        >>> print(date_obj.latest_data)
        2023-06-10 00:00:00-04:00
        >>> print(date_obj.date_string)
        20230610
    """

    def __init__(self):
        """
        Initializes the dataDate object and determines the latest date for SNODAS data download and processing.
        """
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


class file:
    """
    A class for downloading and processing SNODAS data.

    This class handles the downloading, extraction, and processing of SNODAS data for a given date.
    It creates the necessary directories, downloads the data, extracts the compressed files,
    and prepares the data for further processing.

    Attributes:
        date (dataDate): A dataDate object containing the date information for the data download.
        dir (directory): A directory object containing the paths for various directories used in the processing.
        address (str): The URL address for downloading the SNODAS data.

    Methods:
        download(): Downloads the SNODAS data if it hasn't been downloaded already.
        extractTAR(): Extracts the downloaded TAR file.
        extractGZ(): Extracts all GZ files from the extracted TAR file.
    """
    def __init__(self, date, directory):
        """
        Initializes the file object with the given date and directory information.

        Args:
            date (dataDate): A dataDate object containing the date information for the data download.
            directory (directory): A directory object containing the paths for various directories used in the processing.
        """
        self.date = date
        self.dir = directory
        self.dir.create()
        self.address = f"https://noaadata.apps.nsidc.org/NOAA/G02158/unmasked/{self.date.year}/{self.date.month}_{self.date.monthAbbrv}/SNODAS_unmasked_{self.date.year}{self.date.month}{self.date.day}.tar"

    def download(self):
        """
        Downloads the SNODAS data if it hasn't been downloaded already.

        This method checks if the SNODAS data file has already been downloaded.
        If the file doesn't exist, it downloads the data from the specified URL address.
        If the file already exists, it prints a message indicating that the file has been downloaded.
        """
        if not isfile(self.dir.download):
            # Set the no_proxy environment variable to allow downloading without a proxy
            environ["no_proxy"] = "*"
            print(urlretrieve(self.address, self.dir.download))
        else:
            print("file already downloaded; proceeding")

    def extractTAR(self):
        """
        Extracts the downloaded TAR file.

        This method extracts the downloaded TAR file into the specified extraction directory.
        The extracted files are used for further processing.

        Returns:
            str: The path to the directory where the TAR file was extracted.
        """
        unpack_archive(self.dir.download, self.dir.extract)
        return self.dir.extract

    def extractGZ(self):
        """
        Extracts all GZ files from the extracted TAR file and removes the original GZ files.

        This method navigates to the directory where the TAR file was extracted.
        It then iterates through all files in the directory and checks for files with the '.gz' extension.
        For each GZ file found, it extracts the contents and creates a new file without the '.gz' extension.
        After extracting the contents, the original GZ file is removed.
        Finally, the method changes the current working directory back to the original directory.
        """
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
        """
        Initializes the GTIFF class for processing individual GeoTIFF files.

        Args:
            filename (str): The base filename of the GeoTIFF files (without extensions).
            directory (object): A directory object containing the necessary paths.

        Attributes:
            txt (str): The file path for the associated .txt file.
            dat (str): The file path for the associated .dat file.
            hdr (str): The file path for the associated .hdr file.
            metadata (dict): A dictionary containing the metadata read from the .txt file.
        """
        self.txt = join(directory.extract, f"{filename}.txt")  # set .txt file path
        self.dat = join(directory.extract, f"{filename}.dat")  # set .dat file path
        self.hdr = join(directory.extract, f"{filename}.hdr")
        self.metadata = read_txt_vars(self.txt)

    def stringHDR(self):
        """
        Generates the text content for the ENVI header file (.hdr) based on the metadata.

        Returns:
            str: The text content for the ENVI header file.
        """
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
        """
        Creates the ENVI header file (.hdr) with the content generated from the stringHDR method.

        Returns:
            str: The file path of the created .hdr file.
        """
        self.stringHDR()
        with open(self.hdr, "w") as hdr:
            hdr.write(self.envi)
        return self.hdr

    def process(self, dir, filename):
        """
        Processes the .dat file and generates a GeoTIFF file with the specified filename.

        Args:
            dir (object): A directory object containing the necessary paths.
            filename (str): The desired filename for the output GeoTIFF file.
        """
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
        """
        Applies color relief to the GeoTIFF file using a color table file.

        Args:
            dir (object): A directory object containing the necessary paths.
            colortxt (str, optional): The file path of the color table file. If not provided,
                the default file path is constructed based on the GTIFF name.
            output_file (str, optional): The file path for the output GeoTIFF file with color relief.
                If not provided, the original GeoTIFF file will be overwritten.

        This method calls the 'gdaldem color-relief' command in the shell to apply color relief
        to the GeoTIFF file using the specified color table file. The '-alpha' option is used to
        preserve the alpha channel (if present) in the output file.
        """
        if output_file is None:
            output_file = self.fullPath
        if colortxt is None:
            colortxt = join(dir.colortables, f"{self.name}.txt")
        cmd = f"gdaldem color-relief {self.fullPath} {colortxt} {output_file} -alpha"
        check_call(cmd, shell=True)

    def convertToInches(self):
        """
        This method is a placeholder for future work related to converting the SNODAS snow depth data
        to inches.
        """
        pass  # future work

class directory:  # directory manager
    def __init__(self, date):
        """
        Initializes the directory object with paths and filenames based on the provided date.

        Args:
            date (dataDate): A dataDate object containing the current date information.
        """
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
        self.styles = join(self.workingDirectory, "styles")
        self.folders = [
            self.data,
            self.tmp,
            self.finalData,
            self.extract,
            self.styles,
        ]
        self.filenames = join(self.workingDirectory, "filenames.txt")
        self.finalNames = read_txt_vars(self.filenames)
        self.environment = join(self.workingDirectory, ".env")

    def create(self):
        """
        Creates directories for storing data, temporary files, and styles.
        """
        for folder in self.folders:
            Path(folder).mkdir(parents=True, exist_ok=True)

    def outputDirs(self):
        """
        Reads the file names from the filenames.txt file and creates a dictionary with the locations to save processed data.

        Returns:
            dict: A dictionary where keys are file descriptions and values are output file paths.
        """
        self.finalNames = read_txt_vars(self.filenames)
        self.outputPaths = {}
        for key in self.finalNames:
            self.outputPaths[key] = join(self.finalData, f"{self.finalNames[key]}.tif")
        return self.outputPaths

    def unzippedName(self, extension, zippedFile):  # refactor extract GZ in future
        """
        This method is a placeholder for future refactoring related to extracting GZ files.
        """
        pass


class server:
    def __init__(self, directory):
        """
        Initialize a server instance with the given directory.

        Args:
            directory (object): A directory object containing the necessary information
                for the server, such as the styles folder path.
        """
        self.directory = directory
        self.HOST =getenv("GEOSERVER_ADDRESS")
        self.USERNAME = getenv("GEOSERVER_USERNAME")
        self.PASSWORD = getenv("GEOSERVER_PASS")
        self.geoserver = Catalog(self.HOST, self.USERNAME, self.PASSWORD)
        self.geoserver

    def upload_data(self, data_name, workspace, local_path):
        """
        Upload geospatial data to the GeoServer instance.

        Args:
            data_name (str): The name of the data to be uploaded.
            workspace (str): The workspace in GeoServer where the data will be uploaded.
            local_path (str): The local file path of the data to be uploaded.

        Returns:
            A CoverageStore object representing the uploaded data.
        """
        return self.geoserver.create_coveragestore(
            data_name,
            workspace=workspace,
            path=local_path,
            upload_data=True,
            overwrite=True,
        )

    def style_data(self, layer_name, style_name):
        """
        Styles a GeoServer layer with the specified style.

        This method first checks if the specified style exists in the GeoServer instance.
        If the style does not exist, it uploads the style using the `upload_style` method.
        Then, it retrieves the layer object from the GeoServer instance using the provided
        `layer_name`. It constructs an XML string with the `style_name` to be set as the
        default style for the layer.

        Finally, it sends a PUT request to the GeoServer REST API using cURL to set the
        default style for the layer.

        As far as I can tell there is no way to set a default style for a layer using the
        geoserver-restconfig module.

        Args:
            layer_name (str): The name of the layer to be styled.
            style_name (str): The name of the style to be applied to the layer.
        """
        if self.geoserver.get_style(name=style_name) is None:
            print("Style does not exist, uploading new style")
            self.upload_style(style_name)

        layer = self.geoserver.get_layer(layer_name)
        style = f"<layer><defaultStyle><name>{style_name}</name></defaultStyle></layer>"
        cmd = f'curl -u {self.USERNAME}:{self.PASSWORD} -XPUT -H "Content-type: text/xml" -d "{style}" {self.HOST}/layers/SNODAS:{layer.name}'
        system(cmd)

    def upload_folder(self, workspace, folder_path):
        """
        Upload all GeoTIFF files from a specified folder to the GeoServer instance.

        Args:
            workspace (str): The workspace in GeoServer where the data will be uploaded.
            folder_path (str): The local path of the folder containing the GeoTIFF files.
        """
        for data in listdir(folder_path):
            if data.endswith(".tif"):
                data_path = join(folder_path, data)
                name = (path.basename(data)).rsplit(".", 1)[0]
                self.upload_data(name, workspace, data_path)

    def delete_data(self, data_name, workspace):
        """
        Delete geospatial data from the GeoServer instance.

        Args:
            data_name (str): The name of the data to be deleted.
            workspace (str): The workspace in GeoServer where the data is located.

        Returns:
            A boolean indicating whether the deletion was successful.
        """
        store = self.geoserver.get_store(name=data_name, workspace=workspace)
        return self.geoserver.delete(store, purge=True, recurse=True)

    def upload_style(self, style):
        """
        Uploads a specified style to the GeoServer instance.

        This method checks if the specified style file exists in the styles folder
        of the current directory object. If the style file is found, it reads the
        file and creates a new style in the GeoServer instance with the content
        of the file.

        Args:
            style (str): The name of the style to be uploaded.

        Raises:
            Exception: If the specified style file is not found in the styles folder.
        """
        style_files = listdir(self.directory.styles)
        available_styles = [
            strip_extension(path.basename(file)) for file in style_files
        ]
        if style in available_styles:
            style_file = join(self.directory.styles, f"{style}.sld")
            with open(style_file) as file:
                self.geoserver.create_style(
                    strip_extension(path.basename(style)), file.read()
                )
        else:
            raise Exception(f"Style {style} not found in styles folder.")

    def style_types(self, types_list):
        """
        Style all data stores in GeoServer that have a name matching the provided list of types.

        Args:
            types_list (list): A list of data types (store names) to be styled.
        """
        stores = self.geoserver.get_stores()
        for store in stores:
            data_type = store.name
            if data_type in types_list:
                self.style_data(store.name, data_type)

    def selective_upload(self, workspace, folder_path, selection):
        """
        Upload selected GeoTIFF files from a specified folder to the GeoServer instance.

        Args:
            workspace (str): The workspace in GeoServer where the data will be uploaded.
            folder_path (str): The local path of the folder containing the GeoTIFF files.
            selection (list): A list of file names (without extensions) to be uploaded.
        """
        selection = [f"{file}.tif" for file in selection]
        for file in listdir(folder_path):
            if file in selection:
                data_path = join(folder_path, file)
                name = (path.basename(file)).rsplit(".", 1)[0]
                self.upload_data(name, workspace, data_path)
    
    def check_workspace(self, workspace):
        """
        Check if a workspace exists in the GeoServer instance.
        If the workspace does not exist, create it.

        Args:
            workspace (str): The name of the workspace to check/create.

        Returns:
            None
        """
        workspaces = self.geoserver.get_workspaces()
        if workspace not in workspaces:
            self.geoserver.create_workspace(workspace, workspace)
        else:
            print(f"Workspace '{workspace}' already exists.")


def read_txt_vars(txt):
    """
    Read key-value pairs from a text file and store them in a dictionary.

    Args:
        txt (str): Path to the text file.

    Returns:
        dict: A dictionary containing the key-value pairs read from the file.
    """
    variables = {}
    with open(txt) as varfile:
        for var in varfile:
            (key, val) = var.rstrip().split(": ")
            variables[key] = val
    return variables


def strip_extension(file):
    """
    Remove the first file extension from a file path or name.

    Args:
        file (str): The file path or name.

    Returns:
        str: The file name without the first extension.
    """
    return (path.basename(file)).rsplit(".", 1)[0]


def datetime_from_str(string):
    """
    Convert a string in the format 'YYYYMMDD' to a datetime object in the US/Eastern timezone.

    Args:
        string (str): A string representing a date in the format 'YYYYMMDD'.

    Returns:
        datetime.datetime: A datetime object representing the input date in the US/Eastern timezone.
    """
    tz = timezone("US/Eastern")
    date = datetime.strptime(string, "%Y%m%d").replace(tzinfo=tz)
    return date


def main():
    date = dataDate()
    dir = directory(date)
    current_data = file(date, dir)
    current_data.download()
    current_data.extractTAR()
    current_data.extractGZ()
    current_data.createTiffs()
    current_data.cleantemp()
    verty = server(dir)
    verty.selective_upload("SNODAS", current_data.dir.finalData, ["snowdepth", "swe"])
    verty.style_types(["snowdepth", "swe"])


if __name__ == "__main__":
    main()

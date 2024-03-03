import unittest
from os.path import exists

from snoserve import GTIFF, dataDate, directory, file, server


class TestSNOserve(unittest.TestCase):
    def setUp(self):
        self.date = dataDate()
        self.file = file(self.date)
        self.directory = directory(self.date)
        #self.gTiff = GTIFF("test_file", self.directory)
        self.server = server()

    def test_dataDate(self):
        self.assertIsNotNone(self.date.latest_data)
        self.assertIsNotNone(self.date.year)
        self.assertIsNotNone(self.date.day)
        self.assertIsNotNone(self.date.month)
        self.assertIsNotNone(self.date.date_string)
        self.assertIsNotNone(self.date.monthAbbrv)

    def test_file(self):
        self.assertIsNotNone(self.file.date)
        self.assertIsNotNone(self.file.dir)
        self.assertIsNotNone(self.file.address)

    def test_directory(self):
        self.directory.create()
        for folder in self.directory.folders:
            self.assertTrue(exists(folder))

    """ def test_GTIFF(self):
        self.assertIsNotNone(self.gTiff.txt)
        self.assertIsNotNone(self.gTiff.dat)
        self.assertIsNotNone(self.gTiff.hdr)
        self.assertIsNotNone(self.gTiff.metadata)
     """        
    def test_server(self):
        self.assertIsNotNone(self.server.HOST)
        self.assertIsNotNone(self.server.USERNAME)
        self.assertIsNotNone(self.server.PASSWORD)
        self.assertIsNotNone(self.server.geoserver)


if __name__ == "__main__":
    unittest.main()

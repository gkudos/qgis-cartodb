from config import *

import logging
import unittest
import sys

from PyQt4.QtCore import QObject, QEventLoop, pyqtSlot
from PyQt4.QtGui import QApplication
from cartodb.cartodbapi import CartoDBApi

import json

_instance = None


class SignalsObject(QObject):
    def __init__(self, test):
        QObject.__init__(self)
        self.test = test

    @pyqtSlot(dict)
    def cb_show_user_data(self, data):
        self.test.logger.debug("*******************************************************************************")
        self.test.logger.debug("User data loaded: " + json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))
        self.test.logger.debug("*******************************************************************************")
        self.test.assertTrue(data['username'] == cartodb_user)

    @pyqtSlot(dict)
    def cb_show_user_tables(self, data):
        self.test.logger.debug("*******************************************************************************")
        self.test.logger.debug("User tables loaded: " + json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))
        self.test.logger.debug("*******************************************************************************")
        self.test.assertTrue(True)

    @pyqtSlot(dict)
    def cb_show_table_data(self, data):
        self.test.logger.debug("*******************************************************************************")
        self.test.logger.debug("Get user table: " + json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))
        self.test.logger.debug("*******************************************************************************")
        self.test.assertTrue(True)


class UsesQApplication(unittest.TestCase):
    '''Helper class to provide QApplication instances'''

    qapplication = True

    def setUp(self):
        '''Creates the QApplication instance'''

        # Simple way of making instance a singleton
        super(UsesQApplication, self).setUp()
        global _instance
        if _instance is None:
            _instance = QApplication([])

        self.app = _instance

    def tearDown(self):
        '''Deletes the reference owned by self'''
        del self.app
        super(UsesQApplication, self).tearDown()


class CartoDBApiTest(UsesQApplication):
    def setUp(self):
        super(CartoDBApiTest, self).setUp()
        logFormat = '%(asctime)-15s %(name)-12s %(levelname)-8s %(message)s'
        logfile = "output.log"
        logging.basicConfig(level=logging.DEBUG, format=logFormat, filename=logfile, filemode='w', encoding="UTF-8")
        self.logger = logging.getLogger("CartoDBApiTest")
        self.logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        self.logger.addHandler(ch)

        self.signalsObject = SignalsObject(self)

    def tearDown(self):
        super(CartoDBApiTest, self).tearDown()

    @unittest.skip("testing skipping")
    def test_show_user_data(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest get user details for: ' + cartodb_user)
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_show_user_data)
        cartodbApi.getUserDetails()

    @unittest.skip("testing skipping")
    def test_show_user_tables(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest get user tables for: ' + cartodb_user)
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_show_user_tables)
        cartodbApi.getUserTables()

    def test_get_table_data(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest table data for: world_borders')
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_show_table_data)
        cartodbApi.getDataFromTable('SELECT * FROM world_borders LIMIT 10')


if __name__ == '__main__':
    # http://cgoldberg.github.io/python-unittest-tutorial/
    unittest.main()

from config import *

import logging
import unittest
import sys

from PyQt4.QtCore import QObject, QEventLoop, pyqtSlot
from PyQt4.QtGui import QApplication
from cartodb.cartodbapi import CartoDBApi

_instance = None


class SignalsObject(QObject):
    def __init__(self, test):
        QObject.__init__(self)
        self.test = test

    @pyqtSlot(str)
    def cb_show_user_data(self, data):
        self.test.logger.debug("Trajo contenido: " + data)


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

    def test_show_user_data(self):
        self.logger.debug('\nTest get user details for: ' + cartodb_user)
        cartodbApi = CartoDBApi(cartodb_user, api_key, True)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_show_user_data)
        cartodbApi.getUserDetails()
        self.assertTrue(True)


if __name__ == '__main__':
    # http://cgoldberg.github.io/python-unittest-tutorial/
    unittest.main()

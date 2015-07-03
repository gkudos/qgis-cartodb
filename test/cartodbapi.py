from config import *

import logging
import unittest
import sys

from PyQt4.QtCore import QObject, QEventLoop, pyqtSlot
from PyQt4.QtGui import QApplication
from cartodb.cartodbapi import CartoDBApi

import json
import os

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
        self.test.assertEqual(data['username'], cartodb_user)

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

    @pyqtSlot(str)
    def cb_download_file(self, filePath):
        self.test.logger.debug("*******************************************************************************")
        self.test.logger.debug("Download user table: " + filePath)
        self.test.logger.debug("*******************************************************************************")
        self.test.assertTrue(os.path.isfile(filePath))

    @pyqtSlot(dict)
    def cb_show_upload_result(self, data):
        self.test.logger.debug("*******************************************************************************")
        self.test.logger.debug("Upload result: " + json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))
        self.test.logger.debug("*******************************************************************************")
        self.test.assertTrue(True)

    @pyqtSlot(dict)
    def cb_show_create_viz_result(self, data):
        self.test.logger.debug("*******************************************************************************")
        self.test.logger.debug("Create viz result: " + json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))
        self.test.logger.debug("*******************************************************************************")
        self.test.assertIsNotNone(data['map_id'])
        self.test.assertEqual(data['tags'][0], 'QGISCartoDB')

    @pyqtSlot(dict)
    def cb_add_layer_to_map_result(self, data):
        self.test.logger.debug("*******************************************************************************")
        self.test.logger.debug("Add layer to map result: " + json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))
        self.test.logger.debug("*******************************************************************************")
        self.test.assertIsNotNone(data['id'])

    @pyqtSlot(dict)
    def cb_get_layers_map_result(self, data):
        self.test.logger.debug("*******************************************************************************")
        self.test.logger.debug("Get layers result: " + json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))
        self.test.logger.debug("*******************************************************************************")
        self.test.assertEqual(data["total_entries"], 3)

    def cb_progress(self, current, total):
        self.test.logger.debug("Current: {:.2f} MB of {:.2f} MB".format(float(current)/1024/1024, float(total)/1024/1024))


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

    @unittest.skip("testing skipping")
    def test_get_table_data(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest table data for: world_borders')
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_show_table_data)
        cartodbApi.getDataFromTable('SELECT * FROM world_borders LIMIT 10')

    def test_download_file(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest download table data for: world_borders')
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_download_file)
        cartodbApi.download('SELECT * FROM world_borders LIMIT 10')

    @unittest.skip("testing skipping")
    def test_upload_file(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest upload shape: constituencies.zip')
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_show_upload_result)
        cartodbApi.progress.connect(self.signalsObject.cb_progress)
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'data')
        path = os.path.join(path, 'constituencies.zip')
        cartodbApi.upload(path)

    @unittest.skip("testing skipping")
    def test_create_viz_from_table(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest create viz from table. Name: Test map from QGISCartoDB')
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_show_create_viz_result)
        cartodbApi.createVizFromTable('test_ideca_manzanas', 'Test map from QGISCartoDB', 'Test map from Description')

    @unittest.skip("testing skipping")
    def test_add_layer_to_map(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest add layer to map. Layer: test_ideca_localidades')
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_add_layer_to_map_result)
        cartoCSS = '#test_ideca_localidades { polygon-fill: #7B00B4; polygon-opacity: 0.6; line-color: #0F3B82; line-width: 0.5; line-opacity: 1; }'
        cartodbApi.addLayerToMap('df48f415-2ed5-4aaa-ac73-ded9d64f5bd3', 'test_ideca_localidades', cartoCSS)

    @unittest.skip("testing skipping")
    def test_get_layers_map(self):
        self.logger.debug("\n*******************************************************************************")
        self.logger.debug('\nTest get layers in map: Test map from QGISCartoDB 3')
        self.logger.debug("\n*******************************************************************************")
        cartodbApi = CartoDBApi(cartodb_user, api_key, is_multiuser)
        cartodbApi.fetchContent.connect(self.signalsObject.cb_get_layers_map_result)
        cartodbApi.getLayersMap('df48f415-2ed5-4aaa-ac73-ded9d64f5bd3')

if __name__ == '__main__':
    # http://cgoldberg.github.io/python-unittest-tutorial/
    unittest.main()

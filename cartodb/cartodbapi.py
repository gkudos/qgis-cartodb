from PyQt4.QtCore import QObject, QUrl, qDebug, QEventLoop, QFile, QFileInfo, pyqtSignal

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QHttpMultiPart, QHttpPart

import urllib

try:
    import json
except ImportError:
    import simplejson as json


class CartoDBApi(QObject):
    fetchContent = pyqtSignal(object)
    progress = pyqtSignal(int, int)

    def __init__(self, cartodbUser, apiKey, multiuser=False, hostname='cartodb.com'):
        QObject.__init__(self)
        self.multiuser = multiuser
        self.apiKey = apiKey
        self.cartodbUser = cartodbUser
        self.hostname = hostname
        self.apiUrl = "https://{}.{}/api/v1/".format(cartodbUser, hostname)

        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.returnFetchContent)

    def _getRequest(self, url):
        request = QNetworkRequest(url)
        request.setRawHeader("Content-Type", "application/json")
        request.setRawHeader('User-Agent', 'QGIS 2.x')
        return request

    def _createMultipart(self, data={}, files={}):
        multiPart = QHttpMultiPart(QHttpMultiPart.FormDataType)
        for key, value in data.items():
            textPart = QHttpPart()
            textPart.setHeader(QNetworkRequest.ContentDispositionHeader, "form-data; name=\"%s\"" % key)
            textPart.setBody(value)
            multiPart.append(textPart)

        for key, file in files.items():
            filePart = QHttpPart()
            # filePart.setHeader(QNetworkRequest::ContentTypeHeader, ...);
            fileName = QFileInfo(file.fileName()).fileName()
            filePart.setHeader(QNetworkRequest.ContentDispositionHeader, "form-data; name=\"%s\"; filename=\"%s\"" % (key, fileName))
            filePart.setBodyDevice(file)
            multiPart.append(filePart)
        return multiPart

    def getUserDetails(self, returnDict=True):
        self.returnDict = returnDict
        url = QUrl(self.apiUrl + "users/{}/?api_key={}".format(self.cartodbUser, self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.get(request)
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self.error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def getUserTables(self, page=1, per_page=20, shared='yes', returnDict=True):
        self.returnDict = returnDict
        payload = {
            'tag_name': '',
            'q': '',
            'page': page,
            'type': '',
            'exclude_shared': 'false',
            'per_page': per_page,
            'tags': '',
            'shared': shared,
            'locked': 'false',
            'only_liked': 'false',
            'order': 'name',
            'types': 'table'
        }
        url = QUrl(self.apiUrl + "viz?api_key={}&{}".format(self.apiKey, urllib.urlencode(payload)))
        request = self._getRequest(url)

        reply = self.manager.get(request)
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self.error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def getDataFromTable(self, sql, returnDict=True):
        self.returnDict = returnDict
        apiUrl = 'http://{}.cartodb.com/api/v2/sql?api_key={}&format=GeoJSON&q={}'.format(self.cartodbUser, self.apiKey, sql)
        url = QUrl(apiUrl)
        request = self._getRequest(url)

        reply = self.manager.get(request)
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self.error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def upload(self, filePath, returnDict=True):
        self.returnDict = returnDict
        file = QFile(filePath)
        file.open(QFile.ReadOnly)
        url = QUrl(self.apiUrl + "imports/?api_key={}".format(self.apiKey))
        files = {'file': file}
        multipart = self._createMultipart(files=files)
        request = QNetworkRequest(url)
        request.setHeader(QNetworkRequest.ContentTypeHeader, 'multipart/form-data; boundary=%s' % multipart.boundary())
        request.setRawHeader('User-Agent', 'QGIS 2.x')
        reply = self.manager.post(request, multipart)
        loop = QEventLoop()
        reply.uploadProgress.connect(self.progressCB)
        reply.error.connect(self.error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def checkUploadStatus(self, id, returnDict=True):
        self.returnDict = returnDict
        url = QUrl(self.apiUrl + "imports/{}/?api_key={}".format(id, self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.get(request)
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self.error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def createVizFromTable(self, table, name, description='', returnDict=True):
        self.returnDict = returnDict
        payload = {
            'type': 'derived',
            'name': name,
            'title': name,
            'description': description,
            'tags': ['QGISCartoDB'],
            "tables": [table]
        }
        url = QUrl(self.apiUrl + "viz/?api_key={}".format(self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.post(request, json.dumps(payload))
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self.error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def addLayerToMap(self, mapId, table, cartoCSS, returnDict=True):
        self.returnDict = returnDict
        payload = {
            'kind': "carto",
            'options': {
                'attribution': "CartoDB",
                'type': "CartoDB",
                'active': 'true',
                'query': '',
                'opacity': '0.99',
                'interactivity': "cartodb_id",
                'interaction': 'true',
                'debug': 'false',
                'tiler_domain': "cartodb.com",
                'tiler_port': "443",
                'tiler_protocol': "https",
                'sql_api_domain': "cartodb.com",
                'sql_api_port': '443',
                'sql_api_protocol': "https",
                'extra_params': {
                    'cache_policy': "persist",
                    'cache_buster': '1430778800940'
                },
                'cdn_url': "",
                'maxZoom': '28',
                'auto_bound': 'false',
                'visible': 'true',
                'sql_domain': "cartodb.com",
                'sql_port': "443",
                'sql_protocol': "https",
                'tile_style_history': [""],
                'style_version': "2.1.1",
                'table_name': table,
                'user_name': self.cartodbUser,
                'tile_style': cartoCSS,

                'wizard_properties': {
                    'type': "polygon",
                    'properties': {}
                },

                'legend': {
                    'type': "none",
                    'show_title': 'false',
                    'title': "",
                    'template': ""
                },
                'order': '2',
                'parent_id': 'null',
                'use_server_style': 'true',
                'stat_tag': mapId,
                'maps_api_template': 'https://{user}.cartodb.com:443',
                'cartodb_logo': 'false',
                'no_cdn': 'false',
                'force_cors': 'true',
                'tile_style_custom': 'false',
                'query_wrapper': 'nil',
                'query_generated': 'false'
            },
            'order': '1',
            'infowindow': {
                'fields': [],
                'template_name': "table/views/infowindow_light",
                'template': "",
                'alternative_names': {},
                'width': '226',
                'maxHeight': '180'
            },
            'tooltip': {
                'fields': []
            },
            'parent_id': 'null',
            'children': []
        }
        qDebug('URL: ' + self.apiUrl + "maps/{}/layers?api_key={}".format(mapId, self.apiKey))
        url = QUrl(self.apiUrl + "maps/{}/layers?api_key={}".format(mapId, self.apiKey))
        request = self._getRequest(url)

        qDebug('Data:' + json.dumps(payload))
        reply = self.manager.post(request, json.dumps(payload, sort_keys=True, indent=2, separators=(',', ': ')))
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self.error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def progressCB(self, breceived, btotal):
        self.progress.emit(breceived, btotal)

    def returnFetchContent(self, reply):
        response = str(reply.readAll())
        # qDebug('Response:' + response)
        # qDebug('Error: ' + str(reply.error()))
        # qDebug('Status: ' + str(reply.rawHeader('Location')))

        if reply.rawHeader('Location') == 'http://cartodb.com/noneuser.html':
            response = '{"error": "User not found"}'
        elif reply.error() == QNetworkReply.AuthenticationRequiredError:
            response = '{"error": "Confirm user credentials"}'

        if self.returnDict:
            self.fetchContent.emit(json.loads(response))
        else:
            self.fetchContent.emit(response)

    def error(self, error):
        qDebug('Error: ' + str(error))

from PyQt4.QtCore import QObject, QUrl, qDebug, QEventLoop, QFile, QFileInfo, QIODevice, pyqtSignal

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QHttpMultiPart, QHttpPart

import tempfile
import urllib

try:
    import json
except ImportError:
    import simplejson as json


class CartoDBApi(QObject):
    fetchContent = pyqtSignal(object)
    progress = pyqtSignal(int, int)
    error = pyqtSignal(object)

    def __init__(self, cartodbUser, apiKey, multiuser=False, hostname='maps.geografia.com.au'):
        QObject.__init__(self)
        self.multiuser = multiuser
        self.apiKey = apiKey
        self.cartodbUser = cartodbUser
        self.hostname = hostname
        self.apiUrl = "https://{}/user/{}/api/v1/".format(hostname, cartodbUser)
        self.returnDict = True

        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.returnFetchContent)

    def _getRequest(self, url):
        request = QNetworkRequest(url)
        request.setRawHeader("Content-Type", "application/json")
        request.setRawHeader('User-Agent', 'QGISCartoDB 0.2.x')
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
        reply.error.connect(self._error)
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
        reply.error.connect(self._error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def getDataFromTable(self, sql, returnDict=True):
        self.returnDict = returnDict
        apiUrl = 'https://{}/user/{}/api/v2/sql?api_key={}&format=GeoJSON&q={}'.format(self.hostname, self.cartodbUser, self.apiKey, sql)
        url = QUrl(apiUrl)
        request = self._getRequest(url)

        reply = self.manager.get(request)
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self._error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def download(self, sql):
        apiUrl = 'https://{}/user/{}/api/v2/sql?api_key={}&format=spatialite&q={}'.format(self.hostname, self.cartodbUser, self.apiKey, sql)
        url = QUrl(apiUrl)

        request = self._getRequest(url)

        def finished(reply):
            tempdir = tempfile.tempdir
            if tempdir is None:
                tempdir = tempfile.mkdtemp()

            tf = tempfile.NamedTemporaryFile(delete=False)
            sqlite = QFile(tf.name)
            tf.close()
            if(sqlite.open(QIODevice.WriteOnly)):
                sqlite.write(reply.readAll())
                sqlite.close()
                self.fetchContent.emit(tf.name)
            else:
                self.error.emit('Error saving downloaded file')

        manager = QNetworkAccessManager()
        manager.finished.connect(finished)

        reply = manager.get(request)
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self._error)
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
        request.setRawHeader('User-Agent', 'QGISCartoDB 0.2.x')
        reply = self.manager.post(request, multipart)
        loop = QEventLoop()
        reply.uploadProgress.connect(self.progressCB)
        reply.error.connect(self._error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def checkUploadStatus(self, id, returnDict=True):
        self.returnDict = returnDict
        url = QUrl(self.apiUrl + "imports/{}/?api_key={}".format(id, self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.get(request)
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self._error)
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
        reply.error.connect(self._error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def updateViz(self, viz, returnDict=True):
        self.returnDict = returnDict
        url = QUrl(self.apiUrl + "viz/{}?api_key={}".format(viz['id'], self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.put(request, json.dumps(viz))
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self._error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def addLayerToMap(self, mapId, layer, returnDict=True):
        self.returnDict = returnDict
        url = QUrl(self.apiUrl + "maps/{}/layers?api_key={}".format(mapId, self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.post(request, json.dumps(layer))
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self._error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def updateLayerInMap(self, mapId, layer, returnDict=True):
        self.returnDict = returnDict
        url = QUrl(self.apiUrl + "maps/{}/layers/{}?api_key={}".format(mapId, layer['id'], self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.put(request, json.dumps(layer))
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self._error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def getLayersMap(self, mapId, returnDict=True):
        self.returnDict = returnDict
        url = QUrl(self.apiUrl + "maps/{}/layers?api_key={}".format(mapId, self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.get(request)
        loop = QEventLoop()
        reply.downloadProgress.connect(self.progressCB)
        reply.error.connect(self._error)
        reply.finished.connect(loop.exit)
        loop.exec_()

    def progressCB(self, breceived, btotal):
        self.progress.emit(breceived, btotal)

    def returnFetchContent(self, reply):
        response = str(reply.readAll())
        # qDebug('Response:' + response)
        # qDebug('Error: ' + str(reply.error()))
        # qDebug('Status: ' + str(reply.rawHeader('Location')))

        if reply.rawHeader('Location') == 'http://cartodb.com/noneuser.html' or \
           reply.rawHeader('Location') == 'https://maps.geografia.com.au/noneuser.html':
            response = '{"error": "User not found"}'
        elif reply.error() == QNetworkReply.AuthenticationRequiredError:
            response = '{"error": "Confirm user credentials"}'

        if self.returnDict:
            try:
                self.fetchContent.emit(json.loads(response))
            except ValueError as e:
                qDebug('Error loading json. {}'.format(response))
                response = '{"error": "Error loading JSON data"}'
                self.fetchContent.emit(json.loads(response))
        else:
            self.fetchContent.emit(response)

    def _error(self, error):
        qDebug('Error: ' + str(error))
        self.error.emit(error)

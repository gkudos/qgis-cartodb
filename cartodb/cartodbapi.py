from PyQt4.QtCore import QObject, QUrl, qDebug, QEventLoop, pyqtSignal

from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

import urllib

try:
    import json
except ImportError:
    import simplejson as json


class CartoDBApi(QObject):
    fetchContent = pyqtSignal(dict)

    def __init__(self, cartodbUser, apiKey, multiuser=False, hostname='cartodb.com'):
        QObject.__init__(self)
        self.multiuser = multiuser
        self.apiKey = apiKey
        self.cartodbUser = cartodbUser
        self.hostname = hostname

        if multiuser:
            self.apiUrl = "https://{}.{}/api/v1/".format(cartodbUser, hostname)
        else:
            self.apiUrl = "https://{}.{}/api/v1/".format(cartodbUser, hostname)

        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.returnFetchContent)

    def _getRequest(self, url):
        request = QNetworkRequest(url)
        request.setRawHeader("Content-Type", "application/json")
        request.setRawHeader('User-Agent', 'QGIS 2.x')
        return request

    def getUserDetails(self):
        url = QUrl(self.apiUrl + "users/{}/?api_key={}".format(self.cartodbUser, self.apiKey))
        request = self._getRequest(url)

        reply = self.manager.get(request)
        loop = QEventLoop()
        reply.finished.connect(loop.exit)
        loop.exec_()

    def getUserTables(self, page=1, per_page=20, shared='yes'):
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
        reply.finished.connect(loop.exit)
        loop.exec_()

    def returnFetchContent(self, reply):
        self.fetchContent.emit(json.loads(str(reply.readAll())))

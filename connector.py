import cookielib
import urllib
import urllib2
from xbmcswift2 import xbmc


class ConnectionBuilder:
    def __init__(self, login, password, addon_id):
        self.login = login
        self.password = password
        self.addon_id = addon_id
        self.cookie_jar = None

    def build_connection(self, cookie_jar=None):
        if cookie_jar is None:
            cookie_jar = cookielib.CookieJar()
        handlers = [urllib2.HTTPCookieProcessor(cookie_jar)]
        opener = urllib2.build_opener(*handlers)
        opener.addheaders = [('User-Agent',
                              'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)'),
                             ('Accept', '*/*'), ('Accept-Language', 'ru-RU')]
        return opener

    def login_or_none(self):
        cookie_jar = cookielib.CookieJar()
        url_opener = self.build_connection(cookie_jar)
        values = {'username': self.login, 'password': self.password}
        data = urllib.urlencode(values)
        request = urllib2.Request("http://kinozal.tv/takelogin.php", data)
        url_opener.open(request)
        authorized = False
        for cook in cookie_jar:
            if cook.name == 'pass':
                authorized = True
                break
        if not authorized:
            return None
        else:
            return cookie_jar

    def build_authorized_connection(self):
        xbmc.log('[%s]: build_authorized_connection: cookie_jar state [%s]' % (self.addon_id, self.cookie_jar), 3)
        if self.cookie_jar is None:
            self.cookie_jar = self.login_or_none()
            if self.cookie_jar is None:
                xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % ('Error', 'Please check credentials', 5000, None))
        xbmc.log('[%s]: build_authorized_connection: logged in cookie_jar state [%s]' % (self.addon_id, self.cookie_jar),
                 3)
        return self.build_connection(self.cookie_jar)
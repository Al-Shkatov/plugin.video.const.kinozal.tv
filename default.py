# -*- coding: utf-8 -*-
import sys
import os
import urllib
import urllib2
import re
import contextlib
import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))

from connector import ConnectionBuilder
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from support.plugin import plugin
from support.common import run_plugin
from xbmcswift2 import xbmcplugin, xbmcgui, xbmc


def show_message(heading, message, times=3000, icon=None):
    try:
        xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (
            heading.encode('utf-8'), message.encode('utf-8'), times, icon.encode('utf-8')))
    except Exception, e:
        xbmc.log('[%s]: showMessage: Transcoding UTF-8 failed [%s]' % (addon_id, e), 2)
        try:
            xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' %
                                (heading, message, times, icon if icon else addon_icon))
        except Exception, e:
            xbmc.log('[%s]: showMessage: exec failed [%s]' % (addon_id, e), 3)


_internal_screen_id = int(sys.argv[1])

__addon__ = plugin.addon

where = ['названии', 'имени актера', 'жанре', 'формула']
show = ['везде', 'фильмы', 'мультфильмы', 'сериалы', 'шоу', 'музыку']
cshow = ['0', '1002', '1003', '1001', '1006', '1004']
form = ['Все', 'DVDRip', 'HDRip', 'HD Blu-Ray и Remux', 'TVRip']
cform = ['0', '1', '3', '4', '5']
ctype = ['Все', 'Золото', 'Серебро']
cfilter = ['0', '11', '12']

try:
    iwhere = int(__addon__.getSetting('where'))
    ishow = int(__addon__.getSetting('show'))
    iform = int(__addon__.getSetting('form'))
    ifilter = int(__addon__.getSetting('filter'))
    iyear = __addon__.getSetting('year')
    querry = __addon__.getSetting('querry')
except:
    __addon__.setSetting('where', '0')
    __addon__.setSetting('show', '0')
    __addon__.setSetting('form', '0')
    __addon__.setSetting('filter', '1')
    __addon__.setSetting('querry', '')
    # import datetime
    __addon__.setSetting('year', '0')  # str(datetime.date.today().year))

__language__ = __addon__.getLocalizedString

addon_icon = __addon__.getAddonInfo('icon')
addon_fanart = __addon__.getAddonInfo('fanart')
addon_path = __addon__.getAddonInfo('path')
addon_type = __addon__.getAddonInfo('type')
addon_id = __addon__.getAddonInfo('id')
addon_author = __addon__.getAddonInfo('author')
addon_name = __addon__.getAddonInfo('name')
addon_version = __addon__.getAddonInfo('version')

ktv_login = __addon__.getSetting('login')
ktv_password = __addon__.getSetting('password')
ktv_folder = __addon__.getSetting('download_path')
ktv_cookies_uid = __addon__.getSetting('cookies_uid')
ktv_cookies_pass = __addon__.getSetting('cookies_pass')

ktv_connection_method = __addon__.getSetting('connection_method')

if not ktv_login or not ktv_password:
    __addon__.openSettings()

connection_builder = ConnectionBuilder(ktv_login, ktv_password, addon_id)

if not ktv_cookies_uid or not ktv_cookies_pass:
    received = None
    cookie_jar = connection_builder.login_or_none()
    if cookie_jar:
        for cook in cookie_jar:
            if cook.name == 'uid':
                ktv_cookies_uid = cook.value
            if cook.name == 'pass':
                ktv_cookies_pass = cook.value
                received = True
    if received:
        __addon__.setSetting('cookies_pass', ktv_cookies_pass)
        __addon__.setSetting('cookies_uid', ktv_cookies_uid)
    else:
        show_message('Error', 'Please check credentials', 5000)
        __addon__.openSettings()

xbmcplugin.setContent(_internal_screen_id, 'movies')


def construct_request(params):
    return '%s?%s' % (sys.argv[0], urllib.urlencode(params))


def http_get(target, post=None):
    try:
        req = urllib2.Request(target, post)
        url_opener = connection_builder.build_connection()
        with contextlib.closing(url_opener.open(req)) as resp:
            http = resp.read()
        return http
    except Exception, e:
        xbmc.log('[%s]: GET EXCEPT [%s]' % (addon_id, e), 4)
        show_message('HTTP ERROR', e.message, 5000)


def main_screen(params):
    place_folder('Закладки', {'func': 'get_bookmarks'})
    place_folder('Главная', {'func': 'get_main', 'link': 'http://kinozal.tv/'})
    place_folder('Топ раздач', {'func': 'get_top'})
    place_folder('Раздачи', {'func': 'get_search'})
    place_folder('Поиск раздач', {'func': 'get_customsearch'})
    xbmc.log('main screen filled')
    xbmcplugin.endOfDirectory(_internal_screen_id, True, False, True)


def place_link(title, params):
    li = xbmcgui.ListItem(title)
    uri = construct_request(params)
    xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, False)


def get_custom(params):
    try:
        par = int(params['par'])
    except:
        par = None

    iwhere = int(__addon__.getSetting('where'))
    ishow = int(__addon__.getSetting('show'))
    iform = int(__addon__.getSetting('form'))
    ifilter = int(__addon__.getSetting('filter'))
    dialog = xbmcgui.Dialog()
    if par == 1:
        iwhere = dialog.select('Фильтр', where)
    if par == 2:
        ishow = dialog.select('Фильтр', show)
    if par == 3:
        iform = dialog.select('Фильтр', form)
    if par == 4:
        ifilter = dialog.select('Фильтр', ctype)

    __addon__.setSetting('where', str(iwhere))
    __addon__.setSetting('show', str(ishow))
    __addon__.setSetting('form', str(iform))
    __addon__.setSetting('filter', str(ifilter))

    xbmc.executebuiltin('Container.Refresh(%s?func=get_customsearch)' % sys.argv[0])


def get_customsearch(params):
    place_link('Искать в %s' % where[iwhere], {'func': 'get_custom', 'par': '1'})
    place_link('Искать %s' % show[ishow], {'func': 'get_custom', 'par': '2'})
    place_link('Формат: %s' % form[iform], {'func': 'get_custom', 'par': '3'})
    place_link('Фильтр: %s' % ctype[ifilter], {'func': 'get_custom', 'par': '4'})
    place_link('Год: %s' % iyear, {'func': 'get_querry', 'par': 'year'})
    place_link('Искать: %s' % querry, {'func': 'get_querry'})
    place_folder('Поиск', {'func': 'get_search', 's': '1'})
    xbmcplugin.endOfDirectory(_internal_screen_id)


def get_querry(params):
    if "par" in params:
        iyear = __addon__.getSetting("year")
        if iyear == '':
            iyear = datetime.date.today().year

        iyear = xbmcgui.Dialog().numeric(int(iyear), 'Год')

        if iyear == '':
            iyear = ""
        elif int(iyear) < 1900:
            iyear = 1900
        elif int(iyear) > int(datetime.date.today().year):
            show_message('', '%s > %s' % (iyear, datetime.date.today().year))
            iyear = datetime.date.today().year
        __addon__.setSetting('year', str(iyear))

    else:
        skbd = xbmc.Keyboard()
        skbd.setHeading('Поиск:')
        skbd.doModal()
        search_str = ""
        if skbd.isConfirmed():
            search_str = skbd.getText()
            params['search'] = search_str.replace(' ', '+').decode('utf-8').encode('cp1251')
        else:
            params['search'] = ''
        __addon__.setSetting('querry', str(search_str))
    xbmc.executebuiltin('Container.Refresh(%s?func=get_customsearch)' % sys.argv[0])


def place_folder(title, params):
    li = xbmcgui.ListItem(title)
    uri = construct_request(params)
    xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, True)


def check_item_by_tytle(title):
    if ("ALAC" in title) or ("Lossless" in title) or ("FLAC" in title):
        return False
    else:
        return True


def get_main(params):
    http = http_get(params['link'])
    beautiful_soup = BeautifulSoup(http)
    wrapper = beautiful_soup.find('div', attrs={'class': 'tp1_border'})
    cont = wrapper.findAll('div', attrs={'class': 'tp1_body'})
    for film in cont:
        title = film.find('a')['title']
        if not check_item_by_tytle(title):
            continue
        img = film.find('a').find('img')['src']
        if 'http' not in img:
            img = 'http://kinozal.tv%s' % img
        info = {}
        desc = '%s' % film.find('div', attrs={'class': 'tp1_desc1'})
        genre = desc[desc.find("<b>Жанр:</b>") + 17:]
        genre = genre[:genre.find("<br />")]
        year = desc[desc.find("<b>Год выпуска:</b>") + 30:]
        year = year[:year.find("<br />")]
        director = desc[desc.find("<b>Режиссер:</b>") + 25:]
        director = director[:director.find("<br />")]
        xinfos = film.find('div', attrs={'class': 'tp1_desc'}).findAll('div')
        plot = ""
        for xdesc in xinfos:
            for tag in xdesc.contents:
                if tag.__class__.__name__ == 'NavigableString':
                    plot += '%s' % tag
                elif tag.name == 'b':
                    plot = plot + '[B]' + tag.getText() + '[/B]'
                elif tag.name == 'br':
                    plot += '\r'

        info["genre"] = genre
        info["year"] = year
        info["plot"] = plot
        info["plotoutline"] = plot
        info["title"] = title
        info["director"] = director

        li = xbmcgui.ListItem(title, title, img, img)
        li.setProperty('fanart_image', img)
        li.setInfo(type="video", infoLabels=info)
        uri = construct_request({
            'func': 'get_info',
            'url': "http://kinozal.tv/" + film.find('a')["href"],
        })
        xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, True)
    xbmcplugin.endOfDirectory(_internal_screen_id)

    xbmc.executebuiltin('Container.SetViewMode(%s)' % 503)


def get_view_mode():
    view_mode = ""
    controls = (50, 51, 500, 501, 508, 503, 504, 515, 505, 511, 550, 551, 560)
    for _id in controls:
        try:
            if xbmc.getCondVisibility("Control.IsVisible(%i)" % _id):
                view_mode = _id
                return view_mode
        except Exception, e:
            xbmc.log('[%s]: VIEW MODE EXCEPT [%s]' % (addon_id, e), 4)
            show_message('GET VIEW MODE ERROR', e.message, 5000)
            pass
    return view_mode


def get_plot(container):
    plot = ""
    for tag in container.contents:
        if tag.__class__.__name__ == 'NavigableString':
            plot += '%s' % tag
        elif tag.name == 'b':
            plot = plot + '[B]' + tag.getText() + '[/B]'
        elif tag.name == 'br':
            plot += '\r'
        elif tag.name == 'a':
            plot = plot + '[I]' + tag.getText() + "[/I]"

    return plot


def get_detail_torrent(container, _index1, _index2):
    tds = container.findAll('td')
    sp = tds[_index1].getText() + "/" + tds[_index1+1].getText()
    title = '[%s]%s' % (sp, tds[_index2].getText())
    url = ''
    if tds[_index2].a:
        url = tds[_index2].a['href']
        if tds[_index2].a['class'] == 'r1':
            title = '[COLOR=FFDCAF35]%s[/COLOR]' % title
        elif tds[_index2].a['class'] == 'r2':
            title = '[COLOR=FFF0A7AD]%s[/COLOR]' % title
        else:
            title = '[COLOR=FFDDDDDD]%s[/COLOR]' % title

    return dict(sp=sp, title=title, url=url)


def get_detail_torr_1(container):
    return get_detail_torrent(container, 3, 0)


def get_detail_torr_2(container):
    return get_detail_torrent(container, 4, 1)


def get_detail_torr3(container):
    return get_detail_torrent(container, 5, 1)


def list_item(img, info, torr):
    detail = get_detail_torr_1(torr)
    title = detail['title']
    url = detail['url']
    li = xbmcgui.ListItem(title)
    li.setProperty('fanart_image', img)
    li.setInfo(type='video', infoLabels=info)
    uri = construct_request({
        'func': 'get_info',
        'url': "http://kinozal.tv/" + url,
    })
    return dict(li=li, folder=True, url=uri, id='')


def get_by(img, info, xdetails):
    lis = []
    for torr in xdetails:
        lis.append(list_item(img, info, torr))
    return lis


def get_by_genre(img, info, _id):
    detail = http_get('http://kinozal.tv/ajax/details_get.php?id=%s&sr=101' % _id)
    bsdetail = BeautifulSoup(detail.decode('cp1251'))
    return get_by(img, info, bsdetail.findAll('tr', attrs={'class': 'first'}))


def get_by_persone(img, info, _id):
    detail = http_get('http://kinozal.tv/ajax/details_get.php?id=%s&sr=102' % _id)
    bsdetail = BeautifulSoup(detail.decode('cp1251'))
    return get_by(img, info, bsdetail.findAll('tr'))


def get_by_seed(img, info, _id):
    detail = http_get('http://kinozal.tv/ajax/details_get.php?id=%s&sr=103' % _id)
    bsdetail = BeautifulSoup(detail.decode('cp1251'))
    return get_by(img, info, bsdetail.findAll('tr'))


def get_by_like(container, img, info):
    lis = []
    for torr in container.div.table.contents:
        if torr['class'] == 'mn':
            continue
        lis.append(list_item(img, info, torr))
    return lis


def get_info(params):
    http = http_get(params["url"])
    beautiful_soup = BeautifulSoup(http)
    wrapper = beautiful_soup.find('div', attrs={'class': 'mn_wrap'})
    if wrapper is None:
        show_message("Ошибка", "Торрент не найден")
        return
    img = wrapper.find('img', attrs={'class': "p200"})["src"]
    if 'http' not in img:
        img = 'http://kinozal.tv%s' % img
    menu = wrapper.find('ul', attrs={"class": "men w200"})
    mitems = menu.findAll('a')
    sp = ""
    fc = 1
    bookmark = None
    for link in mitems:
        if "Раздают" in link.getText().encode('utf-8'):
            sp = link.find('span', attrs={'class': 'floatright'}).getText()
        elif 'Скачивают' in link.getText().encode('utf-8'):
            sp = sp + '/' + link.find('span', attrs={'class': 'floatright'}).getText()
        elif "Список файлов" in link.getText().encode('utf-8'):
            fc = int(link.span.getText())
        elif "Добавить в закладки" in link.getText().encode('utf-8'):
            bookmark = link['href']

    star = menu.find('div', attrs={'class': 'starbar'}).findAll('a')
    tag_title = None
    for tag in wrapper.contents:
        if tag.name == "div":
            tag_title = tag
            break

    title = "[COLOR=FF008BEE][%s][%s]%s[/COLOR]" % (
        star.__len__(), sp.encode('utf-8'), tag_title.h1.a.getText().encode('utf-8'))
    _id = params['url'].split('=')[1]
    link = 'http://kinozal.tv/download.php?id=%s' % _id
    xinfo = wrapper.find('div', attrs={'class': 'mn1_content'}).findAll('div', attrs={'class': 'bx1 justify'})
    is_block = False
    if xinfo.__len__() == 4:
        is_block = True
        title = '[COLOR=FFFF0000]%s[/COLOR]' % xinfo[0].b.getText()
        xinfo = xinfo[2:]
    elif xinfo.__len__() > 2:
        xinfo = xinfo[1:]
    sinfo = '%s' % xinfo[0]
    info = {}
    year = sinfo[sinfo.find('<b>Год выпуска:</b>') + 30:]
    year = year[:year.find('<br />')]
    genre = sinfo[sinfo.find('<b>Жанр:</b>') + 16:]
    genre = genre[:genre.find('<br />')]
    info['year'] = year
    info['genre'] = genre

    plot = get_plot(xinfo[0].h2)
    plot = plot + '\n' + get_plot(xinfo[1].p)

    tech = wrapper.find('div', attrs={'class': 'justify mn2 pad5x5'})
    plot = plot + '\n' + get_plot(tech)
    info['plot'] = plot

    li = xbmcgui.ListItem(title, title, img, img)

    li.setProperty('fanart_image', img)
    li.setInfo(type='video', infoLabels=info)
    if is_block:
        uri = ''
    else:
        uri = construct_request(
            {
                'func': "play",
                'torr_url': link,
                'filename': '[kinozal.tv]id%s.torrent' % _id,
                'img': img,
                'title': title
            })
        if fc == 1:
            li.setProperty('IsPlayable', 'true')

    menulist = []
    if bookmark:
        addbookmarkuri = construct_request({
            'func': 'http_request',
            'url': "http://kinozal.tv/" + bookmark
        })
        menulist.append(('[COLOR FF669933]Добавить[/COLOR][COLOR FFB77D00] в Закладки[/COLOR]',
                         'XBMC.RunPlugin(%s)' % (addbookmarkuri)))

    downloaduri = construct_request({
        'func': 'download',
        'url': link,
        'filename': '[kinozal.tv]id%s.torrent' % _id
    })
    menulist.append(('[COLOR FF669933]Скачать[/COLOR]', 'XBMC.RunPlugin(%s)' % downloaduri))
    li.addContextMenuItems(menulist)

    xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, fc > 1)

    wrapper = wrapper.find('div', attrs={'class': 'mn1_content'})
    bx1 = wrapper.findAll('div', attrs={'class': 'bx1'})
    bx1 = bx1[2]
    lis = []
    for tabs in bx1.div.ul.contents:
        li = xbmcgui.ListItem(tabs.getText().upper().center(32, '-'))
        li.setProperty('fanart_image', img)
        li.setInfo(type='video', infoLabels=info)
        lis.append(dict(li=li, folder=True, url='', id=tabs['id']))

    bx20 = bx1.find('div', attrs={'class': 'justify mn2'})
    lis_like = []
    if bx20.div.table is not None:
        lis_like = get_by_like(bx20, img, info)
    lis_genre = get_by_genre(img, info, _id)
    lis_persone = get_by_persone(img, info, _id)
    lis_seed = get_by_seed(img, info, _id)

    for li1 in lis:
        xbmcplugin.addDirectoryItem(_internal_screen_id, li1['url'], li1['li'], li1['folder'])
        if li1['id'].find('100') > 0:
            for li2 in lis_like:
                xbmcplugin.addDirectoryItem(_internal_screen_id, li2['url'], li2['li'], li2['folder'])
        elif li1['id'].find('101') > 0:
            for li2 in lis_genre:
                xbmcplugin.addDirectoryItem(_internal_screen_id, li2['url'], li2['li'], li2['folder'])
        elif li1['id'].find('102') > 0:
            for li2 in lis_persone:
                xbmcplugin.addDirectoryItem(_internal_screen_id, li2['url'], li2['li'], li2['folder'])
        elif li1['id'].find('103') > 0:
            for li2 in lis_seed:
                xbmcplugin.addDirectoryItem(_internal_screen_id, li2['url'], li2['li'], li2['folder'])
    xbmcplugin.endOfDirectory(_internal_screen_id)

    xbmc.executebuiltin('Container.SetViewMode(%s)' % 504)


def get_search(params):
    try:
        if 's' in params:
            g = int(__addon__.getSetting('where'))
            c = cshow[ishow]
            v = cform[iform]
            w = cfilter[ifilter]
            qu = querry.decode('utf-8').encode('cp1251')
            iyear = __addon__.getSetting('year')
        else:
            g = 0
            c = 0
            v = 0
            w = 0
            qu = ""
            iyear = "0"

        link = 'http://kinozal.tv/browse.php?s=%s&g=%s&c=%s&v=%s&d=%s&w=%s&t=0&f=0' % (
            urllib.quote_plus(qu), g, c, v, iyear, w)

    except Exception, e:
        xbmc.log('[%s]: SEARCH ERROR [%s]' % (addon_id, e), 4)
        show_message('SEARCh ERROR', e.message, 5000)
        return

    http = http_get(link)
    beautiful_soup = BeautifulSoup(http)
    cat = beautiful_soup.findAll('tr')
    leng = len(cat)
    for film in cat:
        try:
            size = film.findAll('td', attrs={'class': 's'})[1].string
            peers = film.findAll('td', attrs={'class': 'sl_s'})[0].string
            seeds = film.findAll('td', attrs={'class': 'sl_p'})[0].string
            xa = film.find('td', attrs={'class': 'nam'}).find('a')
            title = xa.string
            if xa['class'] == 'r1':
                title = '[COLOR=FFDCAF35]%s[/COLOR]' % title
            elif xa['class'] == 'r2':
                title = '[COLOR=FFA0A7AD]%s[/COLOR]' % title
            else:
                title = '[COLOR=FFDDDDDD]%s[/COLOR]' % title
            img = addon_icon
            li = xbmcgui.ListItem(
                '%s\r\n[COLOR=FF008BEE](peers: %s seeds:%s size%s)[/COLOR]' % (title, peers, seeds, size), addon_icon,
                img)
            li.setProperty('fanart_image', img)
            uri = construct_request({
                'func': 'get_info',
                'url': "http://kinozal.tv/" + xa["href"],
            })
            xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, True, totalItems=leng)

        except:
            pass
    xbmcplugin.endOfDirectory(_internal_screen_id)
    xbmc.executebuiltin('Container.SetViewMode(%s)' % 51)


def get_top(params):
    http = http_get('http://kinozal.tv/top.php')
    beautiful_soup = BeautifulSoup(http)
    cat = beautiful_soup.find('select', attrs={"class": "w100p styled"})
    cat = cat.findAll('option')
    for n in cat:
        if int(n['value']) not in [5, 6, 7, 8, 4, 41, 42, 43, 44]:
            li = xbmcgui.ListItem(n.string.encode('utf-8'), addon_icon, addon_icon)
            uri = construct_request({
                'func': 'get_top1',
                'link': 'http://kinozal.tv/top.php?w=0&t=%s&d=0&f=0&s=0' % n['value']
            })
            xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, True)

    xbmcplugin.endOfDirectory(_internal_screen_id)


def get_top1(params):
    http = http_get(params['link'])
    beautiful_soup = BeautifulSoup(http)
    content = beautiful_soup.find('div', attrs={'class': 'bx1 stable'})
    cats = content.findAll('a')
    for m in cats:
        tit = m['title']
        img = m.find('img')['src']
        if 'http' not in img:
            img = 'http://kinozal.tv%s' % img

        li = xbmcgui.ListItem(tit, addon_icon, img)
        li.setProperty('fanart_image', img)
        uri = construct_request({
            'func': 'get_info',
            'url': "http://kinozal.tv/" + m['href'],
        })
        xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, True)
    xbmcplugin.endOfDirectory(_internal_screen_id)
    xbmc.executebuiltin('Container.SetViewMode(%s)' % 500)


def get_folder(params):
    path = ktv_folder
    dir_list = os.listdir(path)
    for fname in dir_list:
        if re.search('[^/]+.torrent', fname):
            tit = fname
            li = xbmcgui.ListItem(fname)
            uri = construct_request({
                'func': 'play',
                'file': fname,
                'img': None,
                'title': tit
            })
            xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, True)
    xbmcplugin.endOfDirectory(_internal_screen_id)


def http_request(params):
    url_opener = connection_builder.build_authorized_connection()
    req = params['url']
    with contextlib.closing(url_opener.open(req)) as resp:
        http = resp.read()
    return http


def del_bookmark(params):
    http_request(params)
    xbmc.executebuiltin("Container.Refresh")


def get_bookmarks(params):
    req = 'http://kinozal.tv/bookmarks.php?type=1'
    url_opener = connection_builder.build_authorized_connection()
    url = url_opener.open(req)
    http = url.read()
    beautiful_soup = BeautifulSoup(http)

    bx20 = beautiful_soup.find('div', attrs={'class': 'content'}).find('div', attrs={'class': 'bx2_0'})
    if bx20:
        table = bx20.table.findAll('tr')

        for line in table:
            if line.has_key('class') and line['class'] == 'mn':
                continue
            desc = get_detail_torr3(line)

            li = xbmcgui.ListItem(desc['title'], addon_icon, addon_icon)
            uri = construct_request({
                'func': 'get_info',
                'url': "http://kinozal.tv/" + desc['url'],
            })
            tds = line.findAll("td", attrs={'class': 's'})
            delbookmarkuri = construct_request({
                'func': 'del_bookmark',
                'url': "http://kinozal.tv/" + tds[tds.__len__() - 1].a['href']
            })
            li.addContextMenuItems([('[COLOR FF669933]Удалить[/COLOR][COLOR FFB77D00] из Закладок[/COLOR]',
                                     'XBMC.RunPlugin(%s)' % delbookmarkuri,)])
            xbmcplugin.addDirectoryItem(_internal_screen_id, uri, li, True)
    xbmcplugin.endOfDirectory(_internal_screen_id)


def download(params):
    torr_link = params['url']
    url_opener = connection_builder.build_authorized_connection()
    request = urllib2.Request(torr_link)
    url = url_opener.open(request)
    red = url.read()
    if '<!DOCTYPE HTML>' in red:
        show_message('Ошибка', 'Проблема при скачивании ')
    filename = xbmc.translatePath(ktv_folder + params['filename'])
    f = open(filename, 'wb')
    f.write(red)
    f.close()
    show_message('Kinozal.TV', 'Торрент-файл скачан')


def play(params):
    from support.torrent import Torrent
    from support import services

    url_opener = connection_builder.build_authorized_connection()
    request = urllib2.Request(params['torr_url'])
    url = url_opener.open(request)

    data = url.read()
    filename = xbmc.translatePath(ktv_folder + params['filename'])
    try:
        f = open(filename, 'wb')
        f.write(data)
        f.close()
    except:
        xbmc.log('[%s]: Cant create file "%s"' % (addon_id, filename), 4)
        show_message('Internal addon error', 'File "%s" not found' % filename, 2000)
        return
    torrent = Torrent(None, data, filename)
    stream = services.torrent_stream()
    player = services.player()

    stream.play(player, torrent, None, 0)


def addplist(params):
    li = xbmcgui.ListItem(params['tt'])
    uri = construct_request({
        'torr_url': params['t'],
        'title': params['tt'].decode('utf-8'),
        'ind': urllib.unquote_plus(params['i']),
        'img': urllib.unquote_plus(params['ii']),
        'func': 'play_url2'
    })
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).add(uri, li)


def get_params(paramstring):
    param = []
    if len(paramstring) >= 2:
        params = paramstring
        cleanedparams = params.replace('?', '')
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    if len(param) > 0:
        for cur in param:
            param[cur] = urllib.unquote_plus(param[cur])
    return param


@plugin.route('/')
def index():
    params = get_params(sys.argv[2])
    try:
        func = params['func']
        del params['func']
    except:
        func = None
        xbmc.log('[%s]: Primary input' % addon_id, 1)
        main_screen(params)
        sys.exit()
    if func is not None:
        try:
            pfunc = globals()[func]
        except:
            pfunc = None
            xbmc.log('[%s]: Function "%s" not found' % (addon_id, func), 4)
            show_message('Internal addon error', 'Function "%s" not found' % func, 2000)
        if pfunc:
            pfunc(params)
            sys.exit()

# if __name__ == '__main__':
run_plugin()

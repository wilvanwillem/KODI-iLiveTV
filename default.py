'''
    iLiveTV XBMC Plugin
    Copyright (C) 2013 dmdsoftware

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import urllib, urllib2
import cgi
import re
import os

import xbmc, xbmcgui, xbmcplugin, xbmcaddon



#helper methods
def log(msg, err=False):
    if err:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGERROR)
    else:
        xbmc.log(addon.getAddonInfo('name') + ': ' + msg, xbmc.LOGDEBUG)

def parse_query(query):
    queries = cgi.parse_qs(query)
    q = {}
    for key, value in queries.items():
        q[key] = value[0]
    q['mode'] = q.get('mode', 'main')
    return q

def addVideo(url, infolabels, label, img='', fanart='', total_items=0,
                   cm=[], cm_replace=False):
    infolabels = decode_dict(infolabels)
#    log('adding video: %s - %s' % (infolabels['title'].decode('utf-8','ignore'), url))
    listitem = xbmcgui.ListItem(label, iconImage=img,
                                thumbnailImage=img)
    listitem.setInfo('video', infolabels)
    listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('fanart_image', fanart)
    if cm:
        listitem.addContextMenuItems(cm, cm_replace)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=False, totalItems=total_items)

def addDirectory(url, title, img='', fanart='', total_items=0):
    log('adding dir: %s - %s' % (title, url))
    listitem = xbmcgui.ListItem(decode(title), iconImage=img, thumbnailImage=img)
    if not fanart:
        fanart = addon.getAddonInfo('path') + '/fanart.jpg'
    listitem.setProperty('fanart_image', fanart)
    xbmcplugin.addDirectoryItem(plugin_handle, url, listitem,
                                isFolder=True, totalItems=total_items)

#http://stackoverflow.com/questions/1208916/decoding-html-entities-with-python/1208931#1208931
def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

def decode(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data).strip()

def decode_dict(data):
    for k, v in data.items():
        if type(v) is str or type(v) is unicode:
            data[k] = decode(v)
    return data



#global variables
plugin_url = sys.argv[0]
plugin_handle = int(sys.argv[1])
plugin_queries = parse_query(sys.argv[2][1:])

addon = xbmcaddon.Addon(id='plugin.video.ilivetv')

try:

    remote_debugger = addon.getSetting('remote_debugger')
    remote_debugger_host = addon.getSetting('remote_debugger_host')
    remote_debugger = 'true'
    remote_debugger_host = 'localhost'
    # append pydev remote debugger
    if remote_debugger == 'true':
        # Make pydev debugger works for auto reload.
        # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace(remote_debugger_host, stdoutToServer=True, stderrToServer=True)
except ImportError:
    sys.stderr.write("Error: " + "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
    sys.exit(1)
except :
    pass


# retrieve settings
user_agent = addon.getSetting('user_agent')
languageFilter = addon.getSetting('filter')

mode = plugin_queries['mode']

#dump a list of videos available to play
if mode == 'main':
    log(mode)

    url = 'https://www.primewire.ag/towatch/ddurdle'
    header = { 'User-Agent' : user_agent }

    req = urllib2.Request(url, None, header)

    try:
      response = urllib2.urlopen(req)
    except urllib2.URLError, e:
      xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30001))
      log(str(e), True)

    response_data = response.read()

    for r in re.finditer('<td align="center"><a href="([^\"]+)">([^\<]+)</a></td>',
                         response_data, re.DOTALL):
        url,title = r.groups()
        addDirectory('plugin://plugin.video.ilivetv/?mode=subpage&url=' + url,title)
#        addDirectory('plugin://plugin.video.layanmovie/?mode=subpage&url=' + url + '?orderby=title',title + addon.getLocalizedString(30002))


#play a URL that is passed in (presumely requires authorizated session)
elif mode == 'subpage':
    url = plugin_queries['url']
    url = 'https://www.primewire.ag'+url

    header = { 'User-Agent' : user_agent }

    req = urllib2.Request(url, None, header)

    try:
      response = urllib2.urlopen(req)
    except urllib2.URLError, e:
      xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30001))
      log(str(e), True)


    response_data = response.read()


#    match = re.compile('previouspostslink href="(.+?)"', re.DOTALL).findall(response_data)
#    for url in match:
#      addDirectory('plugin://plugin.video.layanmovie?mode=subpage&url=' + url,'<< ' + addon.getLocalizedString(30007) + ' <<')

    for r in re.finditer('<a href="([^\"]+)" onClick="return .*?<script type="text/javascript">document.writeln\(\'([^\']+)\'\);</script>',
                         response_data, re.DOTALL):
            url,site = r.groups()
#            addVideo('plugin://plugin.video.primewire/?mode=videopage&url=' + url, { 'title' : site , 'plot' : site },site)
            url = 'https://www.primewire.ag'+url
            url = re.sub('&', '---', url)
            url = re.sub(' ', '+', url)

            addVideo('plugin://plugin.video.ilivetv/?mode=streamurl&domain='+site+'&url=' + url, { 'title' : site , 'plot' : site },site)
#            url = re.sub('---', '&', url)
#            req = urllib2.Request(url, None, header)

#            try:
#                response = urllib2.urlopen(req)
#            except urllib2.URLError, e:
#                log(str(e), True)


    addVideo('plugin://plugin.video.primewire/?mode=videopage&url=' + url, { 'title' : site , 'plot' : site },'---')


    for r in re.finditer('<tbody>.*?</tbody>',
                         response_data, re.DOTALL):
        entry = r.group()


        url = ''
        site = ''
        for r in re.finditer('<a href="([^\"]+)" onClick="(return) .*?',
#    for r in re.finditer('<a href="([^\"]+)" onClick="return .*?<script type="text/javascript">document.writeln(\'([^\']+)\');</script>',
                         entry, re.DOTALL):
            url,urlID = r.groups()


        for r in re.finditer('(document).writeln\(\'([^\']+)\'\)',
#    for r in re.finditer('<a href="([^\"]+)" onClick="return .*?<script type="text/javascript">document.writeln(\'([^\']+)\');</script>',
                         entry, re.DOTALL):
            siteID,site = r.groups()
            addVideo('plugin://plugin.video.primewire/?mode=videopage&url=' + url, { 'title' : site , 'plot' : site },site)



#play a video given its exact-title
elif mode == 'videopage':
    url = plugin_queries['url']
#    title = plugin_queries['title']
    url = 'https://www.primewire.ag'+url

    header = { 'User-Agent' : user_agent }

    req = urllib2.Request(url, None, header)

    try:
      response = urllib2.urlopen(req)
    except urllib2.URLError, e:
      xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(30001))
      log(str(e), True)


    response_data = response.read()


    for r in re.finditer('<iframe src="([^\"]+)" (width=)',
                         response_data, re.DOTALL):
        url,width = r.groups()
        item = xbmcgui.ListItem(path='plugin://plugin.video.gdrive/?mode=streamurl&url=' + url)
        log('play url: ' + 'plugin://plugin.video.gdrive/?mode=streamurl&url=' + url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

#        addVideo('plugin://plugin.video.gdrive?mode=streamurl&url=' + url,
#                             { 'title' : title , 'plot' : title },
#                             img='None')




xbmcplugin.endOfDirectory(plugin_handle)


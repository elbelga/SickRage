# Author: CristianBB
# Greetings to Mr. Pine-apple
#
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import traceback
from six.moves import urllib

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.common import USER_AGENT
from sickbeard.bs4_parser import BS4Parser


class newpct1Provider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "Newpct1")

        self.supportsBacklog = True
        self.onlyspasearch = None
        self.cache = newpct1Cache(self)

        self.urls = {
            'base_url': 'http://www.newpct1.com',
            'search': 'http://www.newpct1.com/index.php?page=buscar'
        }

        self.url = self.urls['base_url']
        self.headers.update({'User-Agent': USER_AGENT})

        """
        Search query:
        http://www.newpct1.com/index.php?page=buscar&categoryIDR=767&categoryID&idioma=1&calidad=HDTV&ordenar=Fecha&inon=Descendente&q=the+strain

        category_=767 => Category Shows
        idioma_=1 => Language Spanish
        calidad_=All=> Quality ALL
        q => Search show
        """

        self.search_params = {
            'categoryIDR': 767,
            'categoryID': '',
            'idioma': 1,
            'calidad': 'HDTV',
            'ordenar': 'Fecha',
            'inon': 'Descendente',
            'q': ''
        }


    def isEnabled(self):
        return self.enabled

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        lang_info = '' if not epObj or not epObj.show else epObj.show.lang

        #Only search if user conditions are true
        if self.onlyspasearch and lang_info != 'es':
            logger.log(u"Show info is not spanish, skipping provider search", logger.DEBUG)
            return results

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)

            for search_string in search_strings[mode]:
                self.search_params.update({'q': search_string.strip()})

                logger.log(u"Search URL: %s" % self.urls['search'] + '?' + urllib.parse.urlencode(self.search_params), logger.DEBUG)
                data = self.getURL(self.urls['search'], post_data=self.search_params, timeout=30)
                if not data:
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        torrent_ul = html.find('ul', 'buscar-list')

                        if len(torrent_ul) < 1:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrent_li = torrent_ul.findAll('li')
                        num_results = len(torrent_li) - 1

                        iteration = 0
                        for row in torrent_li:
                            try:
                                torrent_info = row.find('div', 'info')
                                if torrent_info:
                                    torrent_size = row.findAll('span')[2]
                                    torrent_row = row.findAll('span')[3]
                                    torrent_url = torrent_row.find('a')[0]
                                    download_url = torrent_url.get('href')
                                    title_raw = torrent_url.get('title')
                                    size = self._convertSize(torrent_size.text)

                                    title = self._processTitle(title_raw)

                                    item = title, download_url, size
                                    logger.log(u"Found result: %s " % title, logger.DEBUG)

                                    items[mode].append(item)
                                    iteration += 1

                            except (AttributeError, TypeError):
                                continue

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.WARNING)

            results += items[mode]

        return results

    @staticmethod
    def _convertSize(size):
        size, modifier = size.split(' ')
        size = float(size)
        if modifier in 'KB':
            size = size * 1024
        elif modifier in 'MB':
            size = size * 1024**2
        elif modifier in 'GB':
            size = size * 1024**3
        elif modifier in 'TB':
            size = size * 1024**4
        return int(size)

    def _processTitle(self, title):

        title = title.replace('Descargar ', '')

        #Quality
        title = title.replace('[HDTV]', '[720p HDTV x264]')
        title = title.replace('[HDTV 720p AC3 5.1]', '[720p HDTV x264]')
        title = title.replace('[HDTV 1080p AC3 5.1]', '[1080p HDTV x264]')
        title = title.replace('[DVDRIP]', '[DVDrip x264]')
        title = title.replace('[DVD Rip]', '[DVDrip x264]')
        title = title.replace('[DVDrip]', '[DVDrip x264]')
        title = title.replace('[BLuRayRip]', '[720p BlueRay x264]')
        title = title.replace('[BRrip]', '[720p BlueRay x264]')
        title = title.replace('[BDrip]', '[720p BlueRay x264]')
        title = title.replace('[BluRay Rip]', '[720p BlueRay x264]')
        title = title.replace('[BluRay 720p]', '[720p BlueRay x264]')
        title = title.replace('[BluRay 1080p]', '[1080p BlueRay x264]')
        title = title.replace('[BluRay MicroHD]', '[1080p BlueRay x264]')
        title = title.replace('[MicroHD 1080p]', '[1080p BlueRay x264]')

        return title


class newpct1Cache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 30


provider = newpct1Provider()

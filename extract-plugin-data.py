#!/usr/bin/python

import re
from bs4 import BeautifulSoup
import urllib2
import csv
from datetime import datetime
from agithub.GitHub import GitHub


def get_plugins():
    plugins_page = urllib2.urlopen('http://leafletjs.com/plugins.html').read()
    soup = BeautifulSoup(plugins_page, 'html.parser')

    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 3:
            plugin_link = tds[0].a
            plugin = plugin_link.string
            maintainer_link = tds[2].a
            plugin_url = plugin_link['href']
            maintainer_url = maintainer_link['href']
            maintainer = maintainer_link.string

            yield {
                'name': plugin,
                'url': plugin_url,
                'maintainer': maintainer,
                'maintainer_url': maintainer_url
            }


GITHUB_URL_PATTERNS = [
    re.compile('^(https|http)://github.com/(?P<owner>[\\w\\-]+)/(?P<repo>[\\w\\.\\-]+)/{0,1}$'),
    re.compile('^(https|http)://(?P<owner>[\\w\\-]+)\\.github\\.(com|io)/(?P<repo>[\\w\\-\\.]+)/{0,1}$'),
]


def get_repo_info(url):
    for p in GITHUB_URL_PATTERNS:
        url_match = p.match(url)
        if url_match:
            return {
                'owner': url_match.group('owner'),
                'repo': url_match.group('repo')
            }

    raise Exception('Not a GitHub repo')


def get_plugin_metadata(url, github):
    info = get_repo_info(url)
    result = github.repos[info['owner']][info['repo']].get()
    if result[0] == 200:
        return result[1]
    elif result[0] == 301:
        repo = re.match('https://api.github.com/repositories/([0-9]+)', result[1]['url']).group(1)
        return github.repositories[repo].get()[1]
    else:
        raise Exception('Unexpected result: %d', result[0])


def era(dt):
    LEAFLET_RELEASE_DATES = [
        ('really old', datetime(1970, 1, 1)),
        ('0.4', datetime(2012, 7, 30)),
        ('0.4.3', datetime(2012, 8, 7)),
        ('0.4.5', datetime(2012, 10, 25)),
        ('0.5', datetime(2013, 1, 17)),
        ('0.6', datetime(2013, 6, 26)),
        ('0.7', datetime(2013, 11, 18)),
        ('1.0-beta.1', datetime(2015, 7, 15)),
        ('1.0-beta.2', datetime(2015, 10, 14)),
        ('1.0-rc.1', datetime(2016, 4, 18)),
    ]

    for i in range(0, len(LEAFLET_RELEASE_DATES) - 1):
        if dt < LEAFLET_RELEASE_DATES[i + 1][1]:
            return LEAFLET_RELEASE_DATES[i][0]

    return LEAFLET_RELEASE_DATES[-1][0]


if __name__ == '__main__':
    import sys

    api_token = sys.argv[1]
    github = GitHub(token=api_token)
    writer = csv.writer(sys.stdout)

    writer.writerow(['Name', 'Era', 'Last commit', 'URL', 'Maintainer', 'Maintainer URL'])

    for plugin in get_plugins():
        try:
            metadata = get_plugin_metadata(plugin['url'], github)
            name = metadata['name']
            plugin_era = era(datetime.strptime(metadata['pushed_at'], '%Y-%m-%dT%H:%M:%SZ'))
            pushed_at = metadata['pushed_at']
        except Exception, e:
            sys.stderr.write('%s (%s): %s\n' % (plugin['name'], plugin['url'], str(e)))
            name = plugin['name']
            plugin_era = ''
            pushed_at = ''

        writer.writerow([
            name.encode('utf-8'),
            plugin_era,
            pushed_at,
            plugin['url'],
            plugin['maintainer'].encode('utf-8'),
            plugin['maintainer_url']
        ])
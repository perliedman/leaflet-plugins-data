#!/usr/bin/python

import re
from bs4 import BeautifulSoup
import urllib2
import json
from datetime import datetime
from agithub.GitHub import GitHub
from github_metadata import get_github_metadata

def get_categories():
    plugins_page = urllib2.urlopen('http://leafletjs.com/plugins.html').read()
    soup = BeautifulSoup(plugins_page, 'html.parser')

    for h3 in soup.find_all('h3')[1:]:
        category = h3.string
        description = h3.find_next_sibling('p').string
        plugin_table = h3.find_next_sibling('table')

        yield {
            'name': category,
            'description': description,
            'plugins': [
                [p for p in get_plugins(plugin_table)]
            ]
        }

def get_plugins(plugin_table):
    for tr in plugin_table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 3:
            plugin_link = tds[0].a
            plugin_name = plugin_link.string
            plugin_description = tds[1].string
            maintainer_link = tds[2].a
            plugin_url = plugin_link['href']
            maintainer_url = maintainer_link['href']
            maintainer = maintainer_link.string

            try:
                metadata = get_plugin_metadata(plugin_url)
            except Exception, e:
                sys.stderr.write('%s (%s): %s\n' % (plugin_name, plugin_url, str(e)))
                metadata = {}

            plugin = {
                'name': plugin_name,
                'homepage': plugin_url,
                'description': plugin_description,
                'author': maintainer,
                'author-url': maintainer_url,
            }

            for (k, v) in metadata.items():
                plugin[k] = v

            yield plugin


def get_plugin_metadata(url):
    metadata = get_github_metadata(url, github)
    metadata['plugin_era'] = era(datetime.strptime(metadata['pushed_at'], '%Y-%m-%dT%H:%M:%SZ'))
    return dict([kv for kv in metadata if kv[0] in ['pushed_at']])

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

    print json.dumps([c for c in get_categories()])

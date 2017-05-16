#!/usr/bin/python

import sys
import re
from bs4 import BeautifulSoup
import urllib2
import yaml
from datetime import datetime
from github_metadata import get_github_metadata
from gitlab_metadata import get_gitlab_metadata
import config
from metadata_exception import MetadataException
from yaml_utils import UnsortableOrderedDict

yaml.SafeDumper.add_representer(UnsortableOrderedDict, yaml.representer.SafeRepresenter.represent_dict)

def get_categories():
    plugins_page = urllib2.urlopen('http://leafletjs.com/plugins.html').read()
    soup = BeautifulSoup(plugins_page, 'html.parser')

    for h2 in soup.find_all('h2')[1:]:
        yield {
            'name': unicode(h2.string),
            'description': unicode(h2.find_next_sibling('p').string),
            'subcategories': [sc for sc in get_subcategory(h2)]
        }

def get_subcategory(h2):
    for header in h2.find_next_siblings(['h2', 'h3']):
        if header.name == 'h2':
            break

        h3 = header

        sub_category = unicode(h3.string)
        sub_description = unicode(h3.find_next_sibling('p').string)
        plugin_table = h3.find_next_sibling('table')

        yield UnsortableOrderedDict([
            ['name', sub_category],
            ['description', sub_description],
            ['plugins', [p for p in get_plugins(plugin_table)]]
        ])

def get_plugins(plugin_table):
    for tr in plugin_table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 3:
            plugin_link = tds[0].a
            plugin_name = unicode(plugin_link.string)
            plugin_description = ' '.join([unicode(c) for c in tds[1].contents]).strip()
            maintainer_link = tds[2].a
            plugin_url = plugin_link['href']
            maintainer_url = maintainer_link['href']
            maintainer = unicode(maintainer_link.string)

            sys.stderr.write(plugin_name + '\n')

#            try:
            metadata = get_plugin_metadata(plugin_url)
#            except Exception, e:
#                sys.stderr.write('%s (%s): %s\n' % (plugin_name, plugin_url, str(e)))
#                metadata = {}

            plugin = UnsortableOrderedDict([
                ('name', plugin_name),
                ('description', plugin_description),
                ('homepage', plugin_url),
                ('author', maintainer),
                ('author-url', maintainer_url),
            ])

            for (k, v) in [kv for kv in metadata.items() if kv[0] in ['pushed_at', 'npm', 'plugin_era']]:
                plugin[k] = v

            yield plugin


def get_plugin_metadata(url):
    metadata_providers = [
        lambda url: get_github_metadata(url, config.github_token),
        lambda url: get_gitlab_metadata(url, config.gitlab_token),
    ]

    metadata = {}
    for metadata_provider in metadata_providers:
        try:
            metadata = metadata_provider(url)
            break
        except MetadataException:
            pass

    if 'pushed_at' in metadata:
        metadata['plugin_era'] = era(datetime.strptime(metadata['pushed_at'], '%Y-%m-%dT%H:%M:%SZ'))

    return metadata

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
        ('1.0-rc.2', datetime(2016, 7, 16)),
        ('1.0-rc.3', datetime(2016, 8, 5)),
        ('1.0.0', datetime(2016, 9, 27)),
        ('1.0.2', datetime(2016, 11, 21)),
        ('1.0.3', datetime(2017, 1, 23)),
    ]

    for i in range(0, len(LEAFLET_RELEASE_DATES) - 1):
        if dt < LEAFLET_RELEASE_DATES[i + 1][1]:
            return LEAFLET_RELEASE_DATES[i][0]

    return LEAFLET_RELEASE_DATES[-1][0]


if __name__ == '__main__':
    print yaml.safe_dump({'categories': [c for c in get_categories()]}, default_flow_style=False, allow_unicode=True)
#    print [c for c in get_categories()]

import urllib2
import re
import json

def get_github_metadata(url, github):
    info = get_repo_info(url)
    result = github.repos[info['owner']][info['repo']].get()
    if result[0] == 200:
        metadata = result[1]
    elif result[0] == 301:
        repo = re.match('https://api.github.com/repositories/([0-9]+)', result[1]['url']).group(1)
        metadata = github.repositories[repo].get()[1]
    else:
        raise Exception('Unexpected result: %d', result[0])

    contents = github.repos[info['owner']][info['repo']].contents.get()[1]
    if contents[0] == 200:
        package_json = [c for c in contents[1] if c['name'] == 'package.json']
        if len(package_json):
            with urllib2.urlopen(package_json['download_url']) as web_request:
                pjson_contents = json.loads(web_request.read())
                metadata['npm'] = pjson_contents['name']

    return metadata

def get_repo_info(url):
    for p in GITHUB_URL_PATTERNS:
        url_match = p.match(url)
        if url_match:
            return {
                'owner': url_match.group('owner'),
                'repo': url_match.group('repo')
            }

    raise Exception('Not a GitHub repo')

GITHUB_URL_PATTERNS = [
    re.compile('^(https|http)://github.com/(?P<owner>[\\w\\-]+)/(?P<repo>[\\w\\.\\-]+)/{0,1}$'),
    re.compile('^(https|http)://(?P<owner>[\\w\\-]+)\\.github\\.(com|io)/(?P<repo>[\\w\\-\\.]+)/{0,1}$'),
]

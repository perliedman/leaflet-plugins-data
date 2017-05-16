import sys
import urllib2
import re
import json
from agithub.GitHub import GitHub
from metadata_exception import MetadataException

def get_github_metadata(url, token):
    info = get_repo_info(url)
    github = GitHub(token=token)
    result = github.repos[info['owner']][info['repo']].get()
    if result[0] == 200:
        metadata = result[1]
    elif result[0] == 301:
        repo = re.match('https://api.github.com/repositories/([0-9]+)', result[1]['url']).group(1)
        metadata = github.repositories[repo].get()[1]
    else:
        raise Exception('Unexpected result: %d', result[0])

    npm_name = get_npm_name(info['owner'], info['repo'], github)
    if not npm_name is None:
        metadata['npm'] = npm_name

    return metadata

def get_npm_name(owner, repo, github):
    #sys.stderr.write('Examining %s/%s for package.json...\n' % (owner, repo))

    contents = github.repos[owner][repo].contents.get()
    if contents[0] == 200:
        #sys.stderr.write('found contents...\n')
        package_json = [c for c in contents[1] if c['name'] == 'package.json']
        if len(package_json):
            #sys.stderr.write('found package.json (%s)\n' % package_json[0]['download_url'])
            url = package_json[0]['download_url']
            web_request = urllib2.urlopen(url)
            try:
                pjson_contents = json.loads(web_request.read())
                #sys.stderr.write('npm name "%s"\n' % pjson_contents['name'])
                if 'name' in pjson_contents:
                    return pjson_contents['name']
            except ValueError:
                sys.stderr.write('Invalid JSON in %s' % url)

    return None

def get_repo_info(url):
    for p in GITHUB_URL_PATTERNS:
        url_match = p.match(url)
        if url_match:
            return {
                'owner': url_match.group('owner'),
                'repo': url_match.group('repo')
            }

    raise MetadataException('Not a GitHub repo')

GITHUB_URL_PATTERNS = [
    re.compile('^(https|http)://github.com/(?P<owner>[\\w\\-]+)/(?P<repo>[\\w\\.\\-]+)/{0,1}$'),
    re.compile('^(https|http)://(?P<owner>[\\w\\-]+)\\.github\\.(com|io)/(?P<repo>[\\w\\-\\.]+)/{0,1}$'),
]


if __name__ == '__main__':
    import sys
    url = sys.argv[1]
    token = sys.argv[2]

    print get_github_metadata(url, token)

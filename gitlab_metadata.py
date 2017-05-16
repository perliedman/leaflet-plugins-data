import sys
import re
import json
from agithub.base import *
from metadata_exception import MetadataException

class GitLab(API):
    def __init__(self, token):
        self.setClient(Client())
        self.setConnectionProperties(ConnectionProperties(
            api_url = 'gitlab.com',
            url_prefix = '/api/v4',
            secure_http = True,
            extra_headers = {
                'PRIVATE-TOKEN': token
            }
            ))

def get_gitlab_metadata(url, token):
    info = get_repo_info(url)
    g = GitLab(token)
    project_id = '%s%%2f%s' % (info['owner'], info['repo'])
    project_request = g.projects[project_id].repository.tree
    sys.stderr.write(str(project_request) + '\n')
    (status, repo) = project_request.get()

    if status == 200:
        metadata = {}

        packagejson_shas = [f['id'] for f in repo if f['name'] == 'package.json']
        if len(packagejson_shas):
            (status, packagejson_contents) = g.projects[project_id].repository.blobs[packagejson_shas[0]].raw.get()
            packagejson = json.loads(packagejson_contents)

            metadata = {
                'npm': packagejson['name']
            }

        return metadata
    else:
        raise Exception('Unexpected result: %d', result[0])

def get_repo_info(url):
    for p in GITLAB_URL_PATTERNS:
        url_match = p.match(url)
        if url_match:
            return {
                'owner': url_match.group('owner'),
                'repo': url_match.group('repo')
            }

    raise MetadataException('Not a GitLab repo')

GITLAB_URL_PATTERNS = [
    re.compile('^(https|http)://gitlab.com/(?P<owner>[\\w\\-]+)/(?P<repo>[\\w\\.\\-]+)/{0,1}$'),
]

if __name__ == '__main__':
    import sys
    url = sys.argv[1]
    token = sys.argv[2]

    print get_gitlab_metadata(url, token)

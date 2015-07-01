#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
# this file is intended to work with Python 2.5

from urlparse import urlparse
import httplib
import sys
import urllib

import simplejson as json


def get_json(conn, path, prefix='/'):
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn.request("GET", prefix + path, params, headers)
    response = conn.getresponse()
    return json.loads(response.read())


def get_current_job_data(prefix='/'):
    return get_json(conn, 'job/' + sys.argv[2] + '/' + sys.argv[3] + '/api/json', prefix)


if __name__ == '__main__':
    artifacts = []
    params = urllib.urlencode({})
    _scheme, netloc, url, _params, _query, _fragment = urlparse(sys.argv[1])
    conn = httplib.HTTPConnection(netloc)
    data = get_current_job_data(prefix=url)
    for action in data['actions']:
        if 'causes' not in action:
            continue
        for cause in action['causes']:
            if 'upstreamBuild' in cause:
                upstream_job_path = u'job/%s/%s' % (cause['upstreamProject'], cause['upstreamBuild'])
                d = get_json(conn, upstream_job_path + '/api/json', prefix=url)
                for artifact in d['artifacts']:
                    artifacts.append(u'%s%s/artifact/%s' % (sys.argv[1], upstream_job_path, artifact['relativePath']))
    conn.close()
    if artifacts:
        fp = open('download-list-%s' % (sys.argv[3]), 'w')
        fp.write(u'\n'.join(artifacts).encode('utf-8'))
        fp.close()

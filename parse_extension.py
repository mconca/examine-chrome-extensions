import json
import os
import sys
import zipfile
import StringIO
import tempfile

import requests

from parse_manifest_and_json import Extension
from utils import download_file, examine, unzip_file


def get_chrome_addon(source):
    dest = tempfile.mkdtemp()
    id = source.split('/')[-1]
    if source.endswith('/'):
        id = source.split('/')[-2]
    url = 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=46.0&x=id%3D' + id + '%26uc'
    destfile = os.path.join(dest, id + '.zip')
    download_file(destfile, url)
    return destfile


def get_addon(source):
    dest = tempfile.mkdtemp()
    id = source.split('/')[-1]
    if source.endswith('/'):
        id = source.split('/')[-2]
    destfile = os.path.join(dest, id)
    download_file(destfile, source)
    return destfile


if __name__=='__main__':
    source = sys.argv[1]
    if source.startswith('https://chrome.google.com/webstore/detail'):
        # Its an add-on on the chrome store, let's get it.
        filename = get_chrome_addon(source)
    elif source.startswith('https://addons.mozilla.org/firefox/downloads/'):
        # Its an add-on on amo, let's get it.
        filename = get_addon(source)
    else:
        raise ValueError('Unknown file source.')

    assert os.path.exists(filename)

    filedir = unzip_file(filename)
    manifest_file = os.path.join(filedir, 'manifest.json')
    api_file = os.path.join(filedir, 'apis.json')
    json.dump(examine(filedir), open(api_file, 'w'))

    ext = Extension(manifest_file, api_file)
    ext.process()

    if ext.missing['apis']:
        print 'APIs missing:'
        print ' ' + ', '.join(ext.missing['apis'])

    if ext.missing['permissions']:
        print 'Permissions missing:'
        print ' ' + ', '.join(ext.missing['permissions'])

    if ext.missing['manifests']:
        print 'Manifest keys missing:'
        print ' ' + ', '.join(ext.missing['manifests'])

    if (not ext.missing['permissions']
        and not ext.missing['apis']
        and not ext.missing['manifests']):
        print 'Nothing missing'

    print 'Try the add-on using: '
    print ' web-ext run -v -s {}'.format(filedir)

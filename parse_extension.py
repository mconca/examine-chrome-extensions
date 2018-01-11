import json
import os
import sys
import zipfile
import io
import tempfile

import requests

from jinja2 import Environment, FileSystemLoader

from parse_manifest_and_json import Extension
from utils import download_file, examine, unzip_file

NOTES = {
    'manifest': {
        'options_page': 'Use options_ui instead. Works in <a href="https://developer.mozilla.org/en-US/Add-ons/WebExtensions/manifest.json/options_ui">Firefox</a> and <a href="https://developer.chrome.com/extensions/optionsV2">Chrome</a>.',
    },
    'permissions': {
        'unlimitedStorage': 'All storage is currently unlimited, see <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1282972">this bug</a>.',
    },
    'apis': {
        'chrome.extension.connectNative': 'Use runtime.connectNative instead.',
        'chrome.permissions.contains': 'Should land in Firefox 54.',
        'chrome.permissions.request': 'Should land in Firefox 54.',
    }
}


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


def format_text(ext):
    if ext.missing['apis']:
        print('APIs used:')
        for api in ext.apis:
            print(' ' + api, end=' ')
            if ext.api_details[api]:
                print(' ' + ', '.join(ext.api_details[api]['platform']))
        print('APIs missing:')
        print(' ' + '\n '.join(ext.missing['apis']))

    if ext.missing['permissions']:
        print('Permissions missing:')
        print(' ' + '\n '.join(ext.missing['permissions']))

    if ext.missing['manifests']:
        print('Manifest keys missing:')
        print(' ' + '\n '.join(ext.missing['manifests']))

    if (not ext.missing['permissions']
        and not ext.missing['apis']
        and not ext.missing['manifests']):
        print('Nothing missing')

    print('Try the add-on using: ')
    print(' web-ext run -v -s {}'.format(filedir))


def format_html(ext, source):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('report.html')
    data = {
        'ext': ext,
        'source': source,
        'notes': NOTES
    }
    html = template.render(data)
    open('index.html', 'w').write(html.encode('utf-8'))


if __name__=='__main__':
    output = sys.argv[1].strip()
    assert output in ['text', 'html'], 'Format invalid: {}'.format(output)

    source = sys.argv[2]
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

    if output == 'text':
        format_text(ext)
    elif output == 'html':
        # This is just a quick prototype.
        format_html(ext, source)
    else:
        raise ValueError('Unknown format.')

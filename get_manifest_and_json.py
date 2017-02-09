import requests
import tempfile
import os
import json
import shutil
import sys

from utils import download_file, examine, unzip_file

unzip = True
parse = True
check_manifest_exists = True
copy_manifest = True

root = os.path.join(os.path.abspath(os.curdir), 'extensions')


def get_extension(id, url, _type, download=True):
    id = id.strip()
    if not id:
        return

    dest = tempfile.mkdtemp()
    os.chdir(dest)

    id = id.split('/')[-1]
    if (check_manifest_exists and
        os.path.exists('%s/%s-apis/%s.json' % (root, _type, id))
        ):
        print 'Manifest %s already exists, skipping' % id
        return


    destfile = os.path.join(dest, id + '.zip')

    print 'Downloading...', id
    try:
        download_file(destfile, url)
        if unzip:
            unzip_file(destfile)

    except (UnicodeDecodeError, requests.exceptions.HTTPError) as exc:
        print exc.message
        print url
        print '...failed'
        return


    if copy_manifest:
        manifest = os.path.join(dest, 'manifest.json')
        os.system('cp manifest.json %s/%s-manifests/%s.json' % (
            root, _type, id))
        print 'Got manifest for', id

    json_file = '%s/%s-apis/%s.json' % (root, _type, id)
    if parse:
        res = examine(dest)
        json.dump(res, open(json_file, 'w'))

    return dest


if __name__=='__main__':
    source = sys.argv[1]
    if source == 'chrome':
        data = json.load(open('chrome-urls.json', 'r'))
        for line in data:
            id = line.split('/')[-1]
            url = (
                'https://clients2.google.com/service/update2/crx'
                '?response=redirect&prodversion=46.0&x=id%3D' + id + '%26uc'
            )
            dest = get_extension(id, url, 'chrome')
            if dest:
                print 'Deleting temp files in...', dest
                shutil.rmtree(dest)

    elif source == 'firefox':
        data = json.load(open('firefox-urls.json', 'r'))
        for line in data:
            id = line.split('/')[6]
            dest = get_extension(id, line, 'firefox')
            if dest:
                print 'Deleting temp files in...', dest
                shutil.rmtree(dest)
    else:
        raise ValueError('Unknown type: {}'.format(source))

import requests
import tempfile
import os
import json
import shutil

from utils import download_file, examine, unzip_file

unzip = True
parse = True
check_manifest_exists = True
copy_manifest = True

root = os.path.join(os.path.abspath(os.curdir), 'extensions')


def get_extension(id, download=True):
    id = id.strip()
    if not id:
        return

    dest = tempfile.mkdtemp()
    os.chdir(dest)

    id = id.split('/')[-1]
    if (check_manifest_exists and
        os.path.exists('%s/apis/%s.json' % (root, id))
        ):
        print 'Manifest %s already exists, skipping' % id
        return


    destfile = os.path.join(dest, id + '.crx')

    print 'Downloading...', id
    try:
        download_file(
            destfile,
            'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=46.0&x=id%3D' + id + '%26uc')
    except:
        print '...failed'
        return

    if unzip:
        unzip_file(destfile)

    if copy_manifest:
        manifest = os.path.join(dest, 'manifest.json')
        os.system('cp manifest.json %s/manifests/%s.json' % (root, id))
        print 'Got manifest for', id

    json_file = '%s/apis/%s.json' % (root, id)
    if parse:
        res = examine(dest)
        json.dump(res, open(json_file, 'w'))

    return dest

if __name__=='__main__':
    data = json.load(open('result.json', 'r'))
    for line in data:
        dest = get_extension(line.split('/')[-1])
        if dest:
            print 'Deleting temp files in...', dest
            shutil.rmtree(dest)

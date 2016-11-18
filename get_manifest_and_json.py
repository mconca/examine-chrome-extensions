import requests
import tempfile
import os
import re
import json
import shutil


def download_file(filename, url):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    print 'Downloaded to', filename
    return filename


unzip = True
parse = True
check_manifest_exists = True
copy_manifest = True

root = os.path.join(os.path.abspath(os.curdir), 'extensions')

regex = re.compile('chrome\.(\w+)\.(\w+)')


def find(filename):
    count = {}
    data = open(filename, 'rb').read()
    if 'chrome.' not in data:
        return

    while data:
        match = regex.search(data)
        if match:
            group = match.group()
            if group == 'chrome.google.com':
                break

            count.setdefault(group, 0)
            count[group] += 1
            data = data[match.end():]
        else:
            break

    return count


def examine(directory):
    count = {}
    print 'Examining ', directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.js'):
                full = os.path.join(root, file)
                res = find(full)
                if res:
                    for k, v in res.items():
                        if not k in count:
                            count[k] = 0
                        count[k] = count[k] + v
    return count


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
        req = download_file(
            destfile,
            'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=46.0&x=id%3D' + id + '%26uc')
    except:
        print '...failed'
        return

    if unzip:
        os.system('unzip -qo %s' % (destfile))

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

import requests
import tempfile
import os, stat
import json
import shutil
import sys
from lxml import html
from utils import download_file, examine, unzip_file

#LIMIT = 10
LIMIT = None

unzip = True
parse = True
check_manifest_exists = True
copy_manifest = True
get_ext_details = True
check_details_exists = True

if os.path.isdir(os.path.join(os.path.abspath(os.curdir), 'temp')):
    myTmp = os.path.join(os.path.abspath(os.curdir), 'temp')
else:
    myTmp = None

root = os.path.join(os.path.abspath(os.curdir), 'extensions')

# XPATH to fields on Chrome details page that we want to scrape
chrome_detail_fields = {
    'Name' : '//h1[@class="e-f-w"]/text()',
    'Users' : '//span[@class="e-f-ih"]/text()',
    'Rating' : '//span[@class="e-f-Sa-L"]/span/meta[1]/@content',
    'Num Ratings' : '//span[@class="e-f-Sa-L"]/span/meta[2]/@content',
    'Developer' : '//a[@class="C-b-p-rc-D-R"]/text()',
}

# Keep a list of bad URLs for extensions that won't download or unzip
# This is useful for restarts
badURLs_file = os.path.join(os.path.abspath(os.curdir), 'badURLs.json')
badURLs = set()
badURLs = set(json.load(open(badURLs_file)))
numBad = len(badURLs)
print(numBad)

def get_extension(id, url, _type, download=True):
    id = id.strip()
    if not id:
        return

    id = id.split('/')[-1]
    if (check_manifest_exists and
        os.path.exists(os.path.join(root, _type + '-manifests', id + '.json'))
        ):
        print('Manifest %s already exists, skipping' % id)
        return

    if id in badURLs:
        return

    dest = tempfile.mkdtemp(dir=myTmp)
    os.chmod(dest, stat.S_IWRITE)
    os.chdir(dest)
    destfile = os.path.join(dest, id + '.zip')

    print('Downloading...', id)
    try:
        download_file(destfile, url)
        try:
            if unzip:
                unzip_file(destfile)
        except:
            print(url)
            print('...unzip failed')
            badURLs.add(id)
            return dest

    except (UnicodeDecodeError, requests.exceptions.HTTPError) as exc:
#        print(exc.message)
        print(url)
        print('...failed')
        badURLs.add(id)
        return dest

    if copy_manifest:
        manifest = os.path.join(dest, 'manifest.json')
        try:
            shutil.copy('manifest.json', os.path.join(root, _type + '-manifests', id + '.json'))
            print('Got manifest for', id)
        except:
            print('No manifest found for', id)

    json_file = os.path.join(root, _type + '-apis', id + '.json')
    if parse:
        res = examine(dest)
        json.dump(res, open(json_file, 'w'))

    return dest

def del_error_func( func, path, exc_info):
    # path contains the path of the file that couldn't be removed
    # func is the delete function that initially failed
    print('Deleting', path)
    os.chmod( path, stat.S_IWRITE )
    func( path )

def get_details(id, details_url):
    res = {}

    id = id.strip()
    if not id:
        return

    id = id.split('/')[-1]
    json_file = os.path.join(root, 'chrome-details', id + '.json')
    if (check_details_exists and os.path.exists(json_file)):
        print('Details %s already exists, skipping' % id)
        return

    try:
        page = requests.get(details_url)
        tree = html.fromstring(page.content)
    except:
        return

    for field, path in chrome_detail_fields.items():
        try:
            val = tree.xpath(path)[0]
        except:
            val = ''
        res[field] = val

    json.dump(res, open(json_file, 'w'))
    print('Got details for', id)
    return

if __name__=='__main__':
    source = sys.argv[1]
    totalExt = 0
    if source == 'chrome':
        data = json.load(open('chrome-urls.json', 'r'))
        for line in data:
            id = line.split('/')[-1]
            url = (
                'https://clients2.google.com/service/update2/crx'
                '?response=redirect&os=cros&arch=x86-64&nacl_arch=x86-64'
                '&prod=chromiumcrx&prodchannel=unknown'
                '&prodversion=9999&x=id%3D' + id + '%26uc'
            )
            dest = get_extension(id, url, 'chrome')
            if dest:
                print('Deleting temp files in...', dest)
                try:
                    shutil.rmtree(dest, onerror=del_error_func)
                except:
                    print('failed.')

            if get_ext_details:
                get_details(id, line)

            totalExt += 1
            if LIMIT and (totalExt > LIMIT):
                break

            if len(badURLs) > numBad:
                json.dump(list(badURLs), open(badURLs_file,'w'))
                numBad += 1

    elif source == 'firefox':
        data = json.load(open('firefox-urls.json', 'r'))
        for line in data:
            id = line.split('/')[6]
            dest = get_extension(id, line, 'firefox')
            if dest:
                print('Deleting temp files in...', dest)
                try:
                    shutil.rmtree(dest, onerror=del_error_func)
                except:
                    print('failed.')

            totalExt += 1
            if LIMIT and (totalExt > LIMIT):
                break

            if len(badURLs) > numBad:
                json.dump(list(badURLs), open(badURLs_file,'w'))
                numBad += 1
    else:
        raise ValueError('Unknown type: {}'.format(source))

import os
import re
import shutil
import requests
from zipfile import ZipFile


def download_file(filename, url):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()


def unzip_file(destfile):
    destdir = os.path.dirname(destfile)
    print(destdir)
    with ZipFile(destfile, 'r') as zippy:
        zippy.extractall(destdir)

    return destdir


regex = re.compile('(chrome|browser)((\.\w+){2,3})')


def find(filename):
    count = {}
    try:
        data = open(filename, 'rb').read().decode()
    except:
        # Probably and encoding error
        return

#    if 'chrome.' not in data:
#        return

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
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.js'):
                full = os.path.join(root, file)
                res = find(full)
                if res:
                    for k, v in list(res.items()):
                        if not k in count:
                            count[k] = 0
                        count[k] = count[k] + v
    return count

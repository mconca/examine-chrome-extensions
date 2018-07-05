import codecs
from collections import Counter
import json
import pprint
import os

# Max number of addons to parse, None is all of them.
#LIMIT = 500
LIMIT = None

class Extension:

    def __init__(self, manifest_file):
        self.type = 'extension'
        self.has_dc = False

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)

        # See if declarativeContent permissions used
        for permission in self.manifest.get('permissions', []):
            if 'declarativeContent' in permission:
                self.has_dc = True


if __name__=='__main__':
    k = 0
    print('Extensions on CWS with declarativeContent permission')
    print('---------------------')
    for filename in os.listdir('extensions/chrome-manifests'):
        if not filename.endswith('.json'):
            continue

        full = os.path.abspath(
            os.path.join('extensions/chrome-manifests', filename))

        # Filter out ones that fail to import.
        try:
            ext = Extension(full)
        except ValueError:
            continue

        if ext.has_dc:
            dets_file = full.replace('chrome-manifests', 'chrome-details')
            data = codecs.open(dets_file, 'r', 'utf-8-sig').read()
            res = json.loads(data)

            id = ext.manifest_filename.split('\\')[-1].split('.json')[0]
            url = 'https://chrome.google.com/webstore/detail/' + id

            # Do a little cleanup on users to make the CSV easier to manipulate
            try:
                users = res['Users'].split()[0]
                users = users.replace(',', '')
                res['Users'] = int(users.replace('+', ''))
            except:
                res['Users'] = 0

            if not res['Name']:
                res['Name'] = '??????????'
            try:
                print(res['Name'] + ',', res['Users'], ',' + url)
            except:
                print('??????????,', res['Users'], ',' + url)

        k += 1
        if LIMIT and k >= LIMIT:
            break

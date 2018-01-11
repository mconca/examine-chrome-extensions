import codecs
from collections import Counter
import json
import pprint
import os

# Max number of addons to parse, None is all of them.
#LIMIT = 5000
LIMIT = None

class Extension:

    def __init__(self, manifest_file, apis_file):
        self.type = 'extension'
        self.is_theme = False
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)

        # Count the permissions used
        for permission in self.manifest.get('permissions', []):
            if 'theme' in permission:
                self.is_theme = True


if __name__=='__main__':
    k = 0
    print('Dynamic Themes on AMO')
    print('---------------------')
    for filename in os.listdir('extensions/firefox-manifests'):
        if not filename.endswith('.json'):
            continue

        full = os.path.abspath(
            os.path.join('extensions/firefox-manifests', filename))
        apis_file = full.replace('firefox-manifests', 'firefox-apis')

        # Filter out ones that fail to import.
        try:
            ext = Extension(full, apis_file)
        except ValueError:
            continue

        if ext.is_theme:
            dets_file = full.replace('firefox-manifests', 'firefox-details')
            data = codecs.open(dets_file, 'r', 'utf-8-sig').read()
            res = json.loads(data)
            print(res['Name'])

        k += 1
        if LIMIT and k >= LIMIT:
            break

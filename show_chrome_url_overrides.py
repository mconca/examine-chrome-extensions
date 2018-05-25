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
        self.has_cuo = False
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)

        # Examine the keys
        for k in self.manifest.keys():
            if k == 'chrome_url_overrides':
                self.has_cuo = True


if __name__=='__main__':
    k = 0
    print('Extensions using chrome_url_overrides on AMO')
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

        if ext.has_cuo:
            dets_file = full.replace('firefox-manifests', 'firefox-details')
            data = codecs.open(dets_file, 'r', 'utf-8-sig').read()
            res = json.loads(data)
            if not res['Name']:
                res['Name'] = '??????????'
            try:
                print(res['Name'] + ',', res['Users'])
            except:
                print('??????????,', res['Users'])

        k += 1
        if LIMIT and k >= LIMIT:
            break

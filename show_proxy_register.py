import codecs
from collections import Counter
import json
import pprint
import os, sys

# Max number of addons to parse, None is all of them.
#LIMIT = 5000
LIMIT = None

class Extension:

    def __init__(self, manifest_file, apis_file):
        self.type = 'extension'
        self.has_ps = False
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(apis_file, 'r', 'utf-8-sig').read()
        self.apis = json.loads(data)

        # Examine the keys
        for api in self.apis:
            if api.startswith('browser.proxy.register'):
                self.has_ps = True


if __name__=='__main__':
    try:
        source = sys.argv[1]
    except:
        source = ''
    
    if source == 'chrome' or source == 'firefox':
        k = 0
        print('Name,Users,ID')
        for filename in os.listdir('extensions/'+source+'-manifests'):
            if not filename.endswith('.json'):
                continue

            full = os.path.abspath(
                os.path.join('extensions/'+source+'-manifests', filename))
            apis_file = full.replace(source+'-manifests', source+'-apis')

            # Filter out ones that fail to import.
            try:
                ext = Extension(full, apis_file)
            except ValueError:
                continue

            if ext.has_ps:
                dets_file = full.replace(source+'-manifests', source+'-details')
                data = codecs.open(dets_file, 'r', 'utf-8-sig').read()
                res = json.loads(data)

                if not res['Name']:
                    res['Name'] = filename
                try:
                    print(res['Name'] + ',', res['Users'], ',', res['ID'])
                except:
                    print(filename + ',', res['Users'], ',', res['ID'])

            k += 1
            if LIMIT and k >= LIMIT:
                break
    else:
        print('Usage:', sys.argv[0], '[ chrome | firefox ]')

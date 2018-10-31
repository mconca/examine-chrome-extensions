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
        self.has_cuo = False
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)

        # Examine the keys
        for k in self.manifest.keys():
            if k == 'chrome_settings_overrides':
                self.has_cuo = True


if __name__=='__main__':
    try:
        source = sys.argv[1]
    except:
        source = ''
    
    if source == 'chrome' or source == 'firefox':
        k = 0
        print('Name,Users,search_provider,homepage,background,content_script,browser_action')
        print('---------------------')
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

            if ext.has_cuo:
                cso = ext.manifest['chrome_settings_overrides']
                has_search = 'search_provider' in cso
                has_homepage = 'homepage' in cso
                has_bs = 'background' in ext.manifest
                has_cs = 'content_script' in ext.manifest
                has_ba = 'browser_action' in ext.manifest

                dets_file = full.replace(source+'-manifests', source+'-details')
                data = codecs.open(dets_file, 'r', 'utf-8-sig').read()
                res = json.loads(data)

                if source == 'chrome' and res['Users']:
                    users = res['Users'].split()[0]
                    users = users.replace(',', '')
                    res['Users'] = int(users.replace('+', ''))

                if not res['Name']:
                    res['Name'] = filename
                try:
                    print(res['Name'] + ',', res['Users'], ',', has_search, ',', has_homepage, ',', has_bs, ',', has_cs, ',', has_ba)
                except:
                    print(filename + ',', res['Users'], ',', has_search, ',', has_homepage, ',', has_bs, ',', has_cs, ',', has_ba)

            k += 1
            if LIMIT and k >= LIMIT:
                break
    else:
        print('Usage:', sys.argv[0], '[ chrome | firefox ]')

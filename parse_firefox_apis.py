import codecs
from collections import Counter
import json
import pprint
import os

importer = Counter({
    'total': 0,
    'extensions': 0,
    'error': 0,
    'browser_namespace': 0,
    'no_apis': 0
})

permissions_counter = Counter()
manifests_counter = Counter()
usage_counter = Counter()
category_counter = Counter()

# Manifest entries to ignore
MAN_IGNORE = [
'manifest_version',
'name',
'version'
]

# Max number of addons to parse, None is all of them.
#LIMIT = 5000
LIMIT = None

class Extension:

    def __init__(self, manifest_file, apis_file):
        self.type = 'extension'
        self.usesBrowserNS = False
        self.no_apis = False
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)
        data = codecs.open(apis_file, 'r', 'utf-8-sig').read()
        self.apis = json.loads(data)

        # Count the APIs used
        self.api_categories = set()
        if len(self.apis) > 0:
            for api in self.apis:
                # Does this extension use the browser namespace?
                if api.startswith('browser.'):
                    self.usesBrowserNS = True
                usage_counter[api.split('.', 1)[-1]] += 1  # only add the part after the namespace

                # Let's count up the major API categories, too
                self.api_categories.add(api.split('.', 2)[1])

            category_counter.update(self.api_categories)
        else:
            self.no_apis = True

        # Count the permissions used
        for permission in self.manifest.get('permissions', []):
            if '://' in permission or '<all_urls>' in permission:
                continue
            if isinstance(permission, dict):
                permission = str(permission)
            permissions_counter[permission] += 1

        # Count the manifest keys used
        for man in self.manifest.keys():
            if man not in MAN_IGNORE:
                manifests_counter[man] += 1


if __name__=='__main__':
    k = 0
    exts = []
    for filename in os.listdir('extensions/firefox-manifests'):
        if not filename.endswith('.json'):
            continue

        importer['total'] += 1
        full = os.path.abspath(
            os.path.join('extensions/firefox-manifests', filename))
        apis_file = full.replace('firefox-manifests', 'firefox-apis')

        # Filter out ones that fail to import.
        try:
            ext = Extension(full, apis_file)
        except ValueError:
            importer['error'] += 1
            continue

        exts.append(ext)
        importer['extensions'] += 1

        k += 1
        if LIMIT and k >= LIMIT:
            break

    for ext in exts:
        if ext.usesBrowserNS:
            importer['browser_namespace'] += 1
        if ext.no_apis:
            importer['no_apis'] += 1

    print('Importer stats')
    print('--------------')

    def display(k, divisor):
        v = importer[k]
        pct = (v / float(importer[divisor])) * 100
        print((' {:6d} {:3.2f}% {}'.format(v, pct, k)))

    display('total', 'total')
    display('extensions', 'total')
    display('error', 'total')
    display('browser_namespace', 'total')
    display('no_apis', 'total')

    ct = 0
    print()
    print('Top API Usage')
    print('------------')
    for k, v in usage_counter.most_common(250):
        ct += 1
        print(' {:3d}'.format(ct), ' {:6d} {}'.format(v, k))

    ct = 0
    print()
    print('Top API Categories')
    print('------------')
    for k, v in category_counter.most_common(250):
        ct += 1
        print(' {:3d}'.format(ct), ' {:6d} {}'.format(v, k))

    ct = 0
    print()
    print('Top Manifest Keys')
    print('------------')
    for k, v in manifests_counter.most_common(250):
        ct += 1
        print(' {:3d}'.format(ct), ' {:6d} {}'.format(v, k))

    ct = 0
    print()
    print('Top Permissions')
    print('------------')
    for k, v in permissions_counter.most_common(250):
        ct += 1
        print(' {:3d}'.format(ct), ' {:6d} {}'.format(v, k))

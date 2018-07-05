import codecs
from collections import Counter
import json
import pprint
import os

# Max number of addons to parse, None is all of them.
#LIMIT = 5000
LIMIT = None

perms = [
    "<all_urls>",
    "activeTab",
    "alarms",
    "background",
    "bookmarks",
    "browserSettings",
    "browsingData",
    "contentSettings",
    "contextMenus",
    "contextualIdentities",
    "cookies",
    "debugger",
    "dns",
    "downloads",
    "downloads.open",
    "find",
    "geolocation",
    "history",
    "identity",
    "idle",
    "management",
    "menus",
    "nativeMessaging",
    "notifications",
    "pageCapture",
    "pkcs11",
    "privacy",
    "proxy",
    "sessions",
    "storage",
    "tabHide",
    "tabs",
#    "theme",
    "topSites",
    "webNavigation",
    "webRequest",
    "webRequestBlocking"
]

class Extension:

    def __init__(self, manifest_file, apis_file):
        self.type = 'extension'
        self.is_theme = False
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)
        data = codecs.open(apis_file, 'r', 'utf-8-sig').read()
        self.apis = json.loads(data)

        # Count the permissions used
        for permission in self.manifest.get('permissions', []):
            if 'theme' in permission:
                self.is_theme = True


if __name__=='__main__':
    k = 0
    # Output header for CSV
    print('Name', end='')
    print(',get(),set()', end='')
    for header in perms:
        print(',', header, end='')
    print()

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
            print(res['Name'], end='')

            # See if extension uses theme.get or theme.set
            for api in ext.apis:
                if api.startswith('browser.theme.get'):
                    print(',1', end='')
                else:
                    print(',0', end='')

                if api.startswith('browser.theme.set'):
                    print(',1', end='')
                else:
                    print(',0', end='')

            ext_perms = ext.manifest.get('permissions', [])
            if 'theme' in ext_perms:
                ext_perms.remove('theme')

            for p in perms:
                if p in ext_perms:
                    print(',1', end='')
                    ext_perms.remove(p)
                else:
                    print(',0', end='')

            # If anything is left, they are likely a host permissions.
            # Print them out so we can check.
            if ext_perms:
                for rem in ext_perms:
                    print(',', rem, end='')

            print()

        k += 1
        if LIMIT and k >= LIMIT:
            break

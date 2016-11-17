import codecs
from collections import Counter
import json
import pprint
import os

importer = Counter({
    'total': 0,
    'success': 0,
    'error': 0,
    'apps': 0,
    'missing_apis': 0,
    'missing_permissions': 0,
    'easy_conversion': 0
})

apis_counter = Counter()
permissions_counter = Counter()

IGNORING = [
    'chrome.storage.local',  # implemented but not read from schema
    'chrome.storage.sync',  # implemented but not read from schema
    'chrome.runtime.id',  # implemented but not read from schema
    'chrome.runtime.lastError',  # implemented but not read from schema
    'chrome.extension.sendMessage',  # deprecated
    'chrome.extension.onRequest',  # deprecated
    'chrome.extension.onMessage',  # deprecated
    'chrome.extension.sendRequest',  # deprecated
    'chrome.app.getDetails',  # deprecated
    'chrome.tabs.getAllInWindow',  # deprecated
    'chrome.tabs.sendRequest', # deprecated
    'chrome.runtime.onInstalled',  # implemented but not read from schema
    'chrome.extension.connect', # deprecated
    'chrome.extension.onConnect',  # deprecated
    'chrome.windows.WINDOW_ID_NONE',  # implemented but not read from schema
    'chrome.windows.WINDOW_ID_CURRENT',  # implemented but not read from schema
    'chrome.extension.lastError',  # deprecated
    # Told in IRC we support these..
    'chrome.extension.inIncognitoContext',
    'chrome.runtime.setUninstallUrl',
]

# An easy way to spot apps.
APP_PERMISSIONS = [
    'syncFileSystem',  # https://developer.chrome.com/apps/syncFileSystem
]

APP_APIS = [
    'chrome.gcm.register',
    'chrome.gcm.onMessage',
    'chrome.app.runtime',
    'chrome.power.requestKeepAwake',
    'chrome.system.memory'
]

PERMISSIONS = [
    '<all_urls>',
    'activeTab',
    'alarms',
    'background',  # We don't really have this in Firefox
    'bookmarks',
    'browserAction',
    'clipboardWrite',
    'contextMenus',
    'cookies',
    'commands',
    'downloads',
    'downloads.open',
    'extension',
    'history',
    'identity',
    'idle',
    'i18n',
    'management',
    'nativeMessaging',
    'tabs',
    'webRequest',
    'webRequestBlocking',
    'notifications',
    'runtime',
    'storage',
    'topSites',
    'webNavigation',
    'windows',
    'unlimitedStorage'  # Well technically everything is unlimited right now.
]

# Max number of addons to parse, None is all of them.
#LIMIT = 50000
LIMIT = None

schemas = json.load(open('schemas.json', 'r'))


def lookup_schema(api):
    if api in IGNORING:
        return True

    api = api.split('.')[1:]
    found = None
    try:
        return schemas[api[0]]['functions'][api[1]]
    except KeyError:
        pass

    try:
        return schemas[api[0]]['events'][api[1]]
    except KeyError:
        pass

    return False


class Extension:

    def __init__(self, filename):
        self.type = 'extension'
        manifest_file = filename
        apis_file = filename.replace('extensions/manifests', 'extensions/apis')
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.id = filename.split('/')[-1]
        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)
        data = codecs.open(apis_file, 'r', 'utf-8-sig').read()
        self.apis = json.loads(data)
        self.missing = {'apis': [], 'permissions': []}

    def is_app(self):
        app = 'app' in self.manifest
        # https://developer.chrome.com/apps/syncFileSystem
        for permission in APP_PERMISSIONS:
            if permission in self.manifest.get('permissions', []):
                app = True

        for api in APP_APIS:
            if api in self.apis:
                app = True

        return app

    def process(self):
        if self.is_app():
            self.type = 'app'
            return

        self.find_missing_apis()
        self.find_missing_permissions()

    def find_missing_apis(self):
        for api in self.apis:
            found = lookup_schema(api)
            if not found:
                self.missing['apis'].append(api)

    def find_missing_permissions(self):
        for permission in self.manifest.get('permissions', []):
            if '://' in permission or '<all_urls>' in permission:
                continue
            if permission not in PERMISSIONS:
                if isinstance(permission, dict):
                    permission = str(permission)
                self.missing['permissions'].append(permission)


if __name__=='__main__':
    k = 0
    exts = []
    for filename in os.listdir('extensions/manifests'):
        if not filename.endswith('.json'):
            continue

        importer['total'] += 1
        full = os.path.abspath(os.path.join('extensions/manifests', filename))

        # Filter out ones that fail to import.
        try:
            ext = Extension(full)
        except ValueError:
            importer['error'] += 1
            continue

        ext.process()

        # Filter out apps.
        if ext.type == 'app':
            importer['apps'] += 1
            continue

        exts.append(ext)
        importer['success'] += 1

        k += 1
        if LIMIT and k >= LIMIT:
            break

    for ext in exts:
        if ext.missing['apis']:
            importer['missing_apis'] += 1
            apis_counter.update(ext.missing['apis'])

        if ext.missing['permissions']:
            importer['missing_permissions'] += 1
            permissions_counter.update(ext.missing['permissions'])

        if not ext.missing['permissions'] and not ext.missing['apis']:
            importer['easy_conversion'] += 1

    print 'Importer stats'
    print '--------------'

    def display(k, divisor):
        v = importer[k]
        pct = (v / float(importer[divisor])) * 100
        print ' {:6d} {:3.2f}% {}'.format(v, pct, k)

    display('success', 'total')
    display('apps', 'total')
    display('error', 'total')
    print
    display('missing_permissions', 'success')
    display('missing_apis', 'success')
    print
    display('easy_conversion', 'success')

    print
    print 'Missing APIs'
    print '------------'
    for k, v in apis_counter.most_common(100):
        print ' {:6d} {}'.format(v, k)

    print
    print 'Missing permissions'
    print '-------------------'
    for k, v in permissions_counter.most_common(100):
        print ' {:6d} {}'.format(v, k)

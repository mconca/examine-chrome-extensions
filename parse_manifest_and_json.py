import codecs
from collections import Counter
import json
import pprint
import os

# See whats missing in a Chrome extension from getting it working in Firefox.
#
# This only really makes sense for Chrome extensions since everything on AMO
# should work on Firefox, right?

importer = Counter({
    'total': 0,
    'success': 0,
    'error': 0,
    'apps': 0,
    'themes': 0,
    'missing_apis': 0,
    'missing_permissions': 0,
    'easy_conversion': 0
})

apis_counter = Counter()
permissions_counter = Counter()
manifests_counter = Counter()
custom_counter = Counter()
custom_counter['externally_connectable'] = 0
custom_counter['externally_connectable_ids'] = []
custom_counter['externally_connectable_matches'] = []
custom_counter['externally_connectable_accepts_tls_channel_id'] = 0
custom_counter['externally_connectable_ids_*'] = 0
custom_counter['externally_connectable_matches_*'] = 0

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
    'chrome.tabs.getSelected',  # this is different in Firefox
    'chrome.tabs.onSelectionChanged',  # this is different in Firefox
    'chrome.runtime.onInstalled',  # implemented but not read from schema
    'chrome.extension.connect', # deprecated
    'chrome.extension.onConnect',  # deprecated
    'chrome.windows.WINDOW_ID_NONE',  # implemented but not read from schema
    'chrome.windows.WINDOW_ID_CURRENT',  # implemented but not read from schema
    'chrome.extension.lastError',  # deprecated
    # Told in IRC we support these..
    'chrome.extension.inIncognitoContext',
    'chrome.runtime.setUninstallUrl',
    # Obvious urls...
    'chrome.googlecode.com',
    # Doesn't exist...
    'chrome.browserAction.show'
]

# An easy way to spot apps.
APP_PERMISSIONS = [
    'syncFileSystem',  # https://developer.chrome.com/apps/syncFileSystem
    'gcm',
]

APP_MANIFESTS = [
    'offline_enabled',
    'fileBrowserHandler'
]

APP_APIS = [
    'chrome.gcm.register',
    'chrome.gcm.onMessage',
    'chrome.app.runtime',
    'chrome.power.requestKeepAwake',
    'chrome.system.memory',
    'chrome.app.runtime',
    'chrome.app.window',
    'chrome.management.launchApp'
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
    'omnibox',
    'tabs',
    'webRequest',
    'webRequestBlocking',
    'notifications',
    'runtime',
    'storage',
    'topSites',
    'webNavigation',
    'windows',
    'unlimitedStorage',  # Well technically everything is unlimited right now.
]

MANIFEST = [
    'name',
    'manifest_version',
    'version',
    'update_url',
    'description',
    'permissions',
    'icons',
    'background',
    'homepage_url',  # we support developers now
    'author',
    'page_action',
    'minimum_chrome_version',  # not relevant and in applications key
    'content_scripts',
    'browser_action',
    'web_accessible_resources',
    'content_security_policy',
    'default_locale',
    'options_ui',
    #'options_page',  # not officially marked as deprecated but close
    'short_name',  # we don't really care about this one
    'clipboardWrite',
    'sessions',
    # Bogus....
    'version_name',
    'key',
    'default_icon',
    'run_at',
    'authors'
]

# Max number of addons to parse, None is all of them.
LIMIT = 500
LIMIT = None

schemas = json.load(open('schemas.json', 'r'))


def lookup_schema(api):
    if api in IGNORING:
        return True

    api = api.split('.')[1:]
    entry = None

    try:
        entry = schemas[api[0]]['functions'][api[1]]
    except KeyError:
        pass

    if not entry:
        try:
            entry = schemas[api[0]]['events'][api[1]]
        except KeyError:
            pass

    if entry:
        return entry['supported']

    return False


class Extension:

    def __init__(self, manifest_file, apis_file):
        self.type = 'extension'
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)
        data = codecs.open(apis_file, 'r', 'utf-8-sig').read()
        self.apis = json.loads(data)
        self.missing = {'apis': [], 'permissions': [], 'manifests': []}

    def get_id(self):
        if 'extensions/manifests' in self.manifest_filename:
            return os.path.splitext(os.path.basename(self.manifest_filename))[0]

    def is_app(self):
        app = 'app' in self.manifest
        for permission in APP_PERMISSIONS:
            if permission in self.manifest.get('permissions', []):
                app = True

        for manifest in self.manifest.keys():
            if manifest in APP_MANIFESTS:
                app = True

        for api in APP_APIS:
            if api in self.apis:
                app = True

        return app

    def is_theme(self):
        return 'theme' in self.manifest

    def process(self):
        if self.is_app():
            self.type = 'app'
            return

        if self.is_theme():
            self.type = 'theme'
            return

        self.find_missing_apis()
        self.find_missing_permissions()
        self.find_missing_manifests()
        self.find_custom()

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

    def find_missing_manifests(self):
        for key in self.manifest.keys():
            if (key not in MANIFEST
                and key not in PERMISSIONS):
                self.missing['manifests'].append(key)

    def find_custom(self):
        if 'externally_connectable' in self.manifest:
            custom_counter['externally_connectable'] += 1
            if 'ids' in self.manifest['externally_connectable']:
                ids = self.manifest['externally_connectable'].get('ids')
                custom_counter['externally_connectable_ids'].append(ids)
                if '*' in ids:
                    custom_counter['externally_connectable_ids_*'] += 1
            if 'matches' in self.manifest['externally_connectable']:
                ms = self.manifest['externally_connectable'].get('matches')
                custom_counter['externally_connectable_matches'].append(ms)
                if '<all_urls>' in ms:
                    custom_counter['externally_connectable_matches_*'] += 1
            if 'accepts_tls_channel_id' in self.manifest['externally_connectable']:
                custom_counter['externally_connectable_accepts_tls_channel_id'] += 1


if __name__=='__main__':
    k = 0
    exts = []
    for filename in os.listdir('extensions/chrome-manifests'):
        if not filename.endswith('.json'):
            continue

        importer['total'] += 1
        full = os.path.abspath(
            os.path.join('extensions/chrome-manifests', filename))
        apis_file = full.replace(
            'extensions/chrome-manifests', 'extensions/chrome-apis')

        # Filter out ones that fail to import.
        try:
            ext = Extension(full, apis_file)
        except ValueError:
            importer['error'] += 1
            continue

        ext.process()

        # Filter out apps.
        if ext.type == 'app':
            importer['apps'] += 1
            continue

        # Filter out themes.
        if ext.type == 'theme':
            importer['themes'] += 1
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

        if ext.missing['manifests']:
            importer['missing_manifests'] += 1
            manifests_counter.update(ext.missing['manifests'])

        if (not ext.missing['permissions']
            and not ext.missing['apis']
            and not ext.missing['manifests']):
            importer['easy_conversion'] += 1

    print 'Importer stats'
    print '--------------'

    def display(k, divisor):
        v = importer[k]
        pct = (v / float(importer[divisor])) * 100
        print ' {:6d} {:3.2f}% {}'.format(v, pct, k)

    display('success', 'total')
    display('apps', 'total')
    display('themes', 'total')
    display('error', 'total')
    print
    display('missing_permissions', 'success')
    display('missing_apis', 'success')
    display('missing_manifests', 'success')
    print
    display('easy_conversion', 'success')

    print 'Missing APIs'
    print '------------'
    for k, v in apis_counter.most_common(100):
        print ' {:6d} {}'.format(v, k)

    print
    print 'Missing permissions'
    print '-------------------'
    for k, v in permissions_counter.most_common(100):
        print ' {:6d} {}'.format(v, k)

    print
    print 'Missing manifests'
    print '-------------------'
    for k, v in manifests_counter.most_common(100):
        print ' {:6d} {}'.format(v, k)

    if custom_counter:
        print
        print 'Custom counter'
        print '--------------'
        for k, v in sorted(custom_counter.most_common(100)):
            if isinstance(v, list):
                avg = sum([len(i) for i in v])/len(v)
                print ' {:6d} {} average'.format(avg, k)
                v = len(v)

            print ' {:6d} {}'.format(v, k)

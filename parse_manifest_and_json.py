import codecs
from collections import Counter
import json, csv
import os

# See whats missing in a Chrome extension from getting it working in Firefox.
#
# This only really makes sense for Chrome extensions since everything on AMO
# should work on Firefox, right?

# Max number of addons to parse, None is all of them.
#LIMIT = 5000
LIMIT = None

write_csv_file = True
check_name_on_AMO = True
AMO_name_set = set()

importer = Counter({
    'total': 0,
    'extensions': 0,
    'error': 0,
    'apps': 0,
    'themes': 0,
    'missing_apis': 0,
    'missing_permissions': 0,
    'easy_conversion': 0,
    'browser_namespace': 0,
    'no_apis': 0
})

apis_counter = Counter()
permissions_counter = Counter()
manifests_counter = Counter()
usage_counter = Counter()
custom_counter = Counter()
custom_counter['externally_connectable'] = 0
custom_counter['externally_connectable_ids'] = []
custom_counter['externally_connectable_matches'] = []
custom_counter['externally_connectable_accepts_tls_channel_id'] = 0
custom_counter['externally_connectable_ids_*'] = 0
custom_counter['externally_connectable_matches_*'] = 0
custom_counter['file:'] = 0

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
    'chrome.windows.WINDOW_ID_CURRENT',
    'chrome.extension.lastError',  # deprecated
    # Told in IRC we support these..
    'chrome.extension.inIncognitoContext',
    'chrome.runtime.setUninstallUrl',
    # Obvious urls...
    'chrome.googlecode.com',
    # Doesn't exist...
    'chrome.browserAction.show',
    # https://dxr.mozilla.org/mozilla-central/source/toolkit/components/extensions/schemas/web_request.json#33
    'chrome.webRequest.ResourceType', # implemented but not read from schema
    # https://dxr.mozilla.org/mozilla-central/source/toolkit/components/extensions/schemas/web_request.json#26
    'chrome.webRequest.MAX_HANDLER_BEHAVIOR_CHANGED_CALLS_PER_10_MINUTES',  # implemented but not read from schema
]

# August, 2017
# The schemas.json file is very old and does not reflect what is currently
# implemented. The script that generated that file is in another project
# called arewewebextensionsyet, but it is very out of date as well. So
# I'm just adding in things I know have landed here.
IGNORING = IGNORING + [
    'chrome.extension.onMessage.addListener',   # deprecated
    'chrome.extension.onRequest.addListener',  # deprecated
    'chrome.extension.onConnect.addListener',  # deprecated
    'chrome.extension.lastError.message',   # deprecated
    'chrome.extension.onRequestExternal.addListener',  # deprecated
    'chrome.tabs.onSelectionChanged.addListener',  # deprecated
    'chrome.tabs.onActiveChanged.addListener',  # deprecated
    'chrome.storage.set',
    'chrome.storage.local.get',
    'chrome.storage.local.set',
    'chrome.storage.local.remove',
    'chrome.storage.local.clear',
    'chrome.storage.sync.get',
    'chrome.storage.sync.set',
    'chrome.storage.sync.remove',
    'chrome.storage.sync.clear',
    'chrome.runtime.lastError.message',
    'chrome.runtime.onInstalled',
    'chrome.runtime.onMessageExternal',  # implemented in 54
    'chrome.runtime.onMessageExternal.addListener',   # implemented in 54
    'chrome.runtime.onConnectExternal',  #implemented in 54
    'chrome.runtime.onConnectExternal.addListener',  # implemented in 54
    'chrome.management.getAll',   # implemented in 55
    'chrome.management.setEnabled',   # implemented in 55
    'chrome.management.get',   # implemented in 56
    'chrome.permissions.request',  # implemented in 55
    'chrome.permissions.remove',  # implemented in 55
    'chrome.permissions.contains',  # implemented in 55
    'chrome.permissions.getAll',  # implemented in 55
    'chrome.webNavigation.onCreatedNavigationTarget.addListener', # implemented in 54
    'chrome.devtools.panels',  # implemented in 54
    'chrome.devtools.panels.create',  # implemented in 54
    'chrome.devtools.inspectedWindow.tabId',  # implemented in 54
    'chrome.devtools.panels.elements', # implemented in 56
    'chrome.devtools.panels.themeName', # implemented in 55
    'chrome.runtime.error',   # not a real API (ext macro, maybe)
    'chrome.tabs.cr_tabs_TabClosed_listeners_added',  # not a real API (ext macro, maybe)
    'chrome.tabs.cr_tabs_TabCreated_listeners_added',  # not a real API (ext macro, maybe)
    'chrome.tabs.cr_tabs_TabSelectionChanged_listeners_added',  # not a real API (ext macro, maybe)
    'chrome.tabs.hasOwnProperty',  # not a real API (ext macro, maybe)
    'chrome.browserAction.set'   # not a real API (ext macro, maybe)
]

# November, 2017
# Additional API to ignore. With this update, I let the browser
# namespace come through, but some libraries, like angular.js,
# also have a broswer namespace that we need to ignore.
FAKE_BROWSER = [
    'browser.defer',   # angular.js
    'browser.defer.cancel',   # angular.js
    'browser.defer.flush',   # angular.js
    'browser.driver.getCurrentUrl',   # angular.js
    'browser.params.browser',    # angular.js
    'browser.deferredFns.length',    # angular.js
    'browser.tabs.getAll',    # kango library
    'browser.event.DOCUMENT_COMPLETE',  # kango library
    'browser.event.TAB_CHANGED',    # kango library
    'browser.event.BEFORE_NAVIGATE',    # kango library
    'browser.part.js',    # kango library
    'browser.oldsafari.version',    # Safari
    'browser.tabs.broadcastMessage',   # Opera?
    'browser.realVersion.split',   # ???
    'browser.version.split',   # ???
    'browser.name.toLowerCase',   # jQuery
    'browswer.js.map',   # AWS
    'chrome.js.map',  # AWS
    'browser.pipe.aria.microsoft',  # Skype
]

IGNORING = IGNORING + FAKE_BROWSER
IGNORING = IGNORING + [
    'browser.storage.local.get',   # implemented in 48
    'browser.storage.local.remove',   # implemented in 48
    'browser.storage.local.set',   # implemented in 48
    'browser.storage.local',    # implemented in 48
    'browser.storage.local.clear',  # implemented in 45
    'browser.storage.sync',  # implemented in 53
    'browser.storage.sync.set',   # implemented in 53
    'browser.storage.sync.get',   # implemented in 53
    'browser.runtime.lastError',   # implemented in 48
    'browser.runtime.id',  # implemented in 45
    'chrome.storage.managed',   # implemented in 57
    'chrome.storage.managed.get',   # implemented in 57
    'chrome.privacy.network',  # implemented in 54
    'chrome.privacy.network.networkPredictionEnabled',  # implemented in 54
    'chrome.privacy.network.peerConnectionEnabled',  # implemented in 55
    'chrome.privacy.network.webRTCIPHandlingPolicy',  # implement in 54
    'chrome.privacy.services.passwordSavingEnabled',  # implemented in 56
    'chrome.privacy.websites.firstPartyIsolate',  # implemented in 58
    'chrome.privacy.websites.hyperlinkAuditingEnabled',  # implemented in 54
    'chrome.privacy.websites.referrersEnabled',  # implemented in 56
    'chrome.privacy.websites.resistFingerprinting',  # implemented in 58
    'chrome.privacy.websites.trackingProtectionMode',  # implemented in 57
    'chrome.tabs.discard',  # implemented in 58
    'chrome.devtools.network.onNavigated',  # implemented in 54
    'chrome.devtools.network.getHAR',  # implemented in 60
    'chrome.devtools.network.onRequestFinished'  # implemented in 60
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
    'chrome.management.launchApp',
    'chrome.app.runtime.onLaunched',
    'chrome.app.window.create',
    'chrome.identity.getAuthToken',
    'chrome.identity.removeCachedAuthToken',
    'chrome.identity.getProfileUserInfo'
]

PERMISSIONS = [
    '<all_urls>',
    'activeTab',
    'alarms',
    'background',  # We don't really have this in Firefox
    'bookmarks',
    'browserAction',
    'clipboardWrite',
    'clipboardRead',
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
    'proxy',
    'browsingData',
    'sessions',
    'geolocation',
    'privacy'
]

MANIFEST = [
    'chrome_url_overrides',
    'incognito',
    'optional_permissions',
    'chrome_settings_overrides',
    'devtools_page',
    'applications',
    'developer',
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
    'options_page',  # not officially marked as deprecated but close
    'short_name',  # we don't really care about this one
    'clipboardWrite',
    'clipboardRead',
    'sessions',
    # Bogus....
    'version_name',
    'key',
    'default_icon',
    'run_at',
    'authors'
]

schemas = json.load(open('schemas.json', 'r'))
dict_schemas = {}

for k, schema in schemas:
    dict_schemas[k] = schema


def get_api(api):
    if 'devtools' in api:
        temp = api.split('.')[1:]
        if len(temp) > 2:
            api = ('.'.join([temp[0], temp[1]]), temp[2])
        else:
            api = temp
    else:
        api = api.split('.')[1:]
    return api


def get_schema_entry(api):
    entry = None
    api_split = get_api(api)

    try:
        entry = dict_schemas[api_split[0]]['schema']['functions'][api_split[1]]
    except KeyError:
        pass

    if not entry:
        try:
            entry = dict_schemas[api_split[0]]['schema']['events'][api_split[1]]
        except KeyError:
            pass

    return entry


def lookup_schema(api, platform):
    if api in FAKE_BROWSER:
        return True

    usage_counter[api] += 1

    if api in IGNORING:
        return True

    schema_entry = get_schema_entry(api)
    api_entry = dict_schemas.get(get_api(api)[0])

    if api_entry and schema_entry and platform in api_entry.get('platform', []):
        return schema_entry['supported']

    return False

def is_name_on_AMO(chromeName):
    if len(AMO_name_set) == 0:
        # First time thru, build the name database
        for filename in os.listdir('extensions/firefox-details'):
            if not filename.endswith('.json'):
                continue

            full = os.path.abspath(os.path.join('extensions/firefox-details', filename))
            res = codecs.open(full, 'r', 'utf-8-sig').read()
            fxdets = json.loads(res)
            AMO_name_set.add(fxdets['Name'])

    if chromeName in AMO_name_set:
        return 'yes'
    else:
        return 'no'


class Extension:

    def __init__(self, manifest_file, apis_file, dets_file):
        self.no_apis = False
        self.type = 'extension'
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)
        data = codecs.open(apis_file, 'r', 'utf-8-sig').read()
        self.apis = json.loads(data)
        data = codecs.open(dets_file, 'r', 'utf-8-sig').read()
        self.details = json.loads(data)
        self.details.update({'Portable':'No', 'Name on AMO':'Unknown', 'Missing API':[],
                             'Missing Permissions':[], 'Missing Manifest Keys':[]})

        if len(self.apis) == 0:
            self.no_apis = True
        self.usesBrowserNS = False
        for api in self.apis:
            if api.startswith('browser.'):
                self.usesBrowserNS = True
        self.missing = {'apis': [], 'permissions': [], 'manifests': []}

        if check_name_on_AMO:
            self.details['Name on AMO'] = is_name_on_AMO(self.details['Name'])

    def get_id(self):
        if 'extensions/manifests' in self.manifest_filename:
            return os.path.splitext(os.path.basename(self.manifest_filename))[0]

    def is_app(self):
        app = 'app' in self.manifest
        for permission in APP_PERMISSIONS:
            if permission in self.manifest.get('permissions', []):
                app = True

        for manifest in list(self.manifest.keys()):
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
            found = lookup_schema(api, 'desktop')
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
        for key in list(self.manifest.keys()):
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

        for permission in self.manifest.get('permissions', []):
            if isinstance(permission, dict):
                continue

            if permission.startswith('file:'):
                custom_counter['file:'] += 1
                continue

    def get_url(self):
        url = 'https://chrome.google.com/webstore/detail/'
        id = self.manifest_filename.split('/')[-1].split('.json')[0]
        return url + id


if __name__=='__main__':
    k = 0
    exts = []
    for filename in os.listdir('extensions/chrome-manifests'):
        if not filename.endswith('.json'):
            continue

        importer['total'] += 1
        full = os.path.abspath(
            os.path.join('extensions/chrome-manifests', filename))
        apis_file = full.replace('chrome-manifests', 'chrome-apis')
        dets_file = full.replace('chrome-manifests', 'chrome-details')

        # Filter out ones that fail to import.
        try:
            ext = Extension(full, apis_file, dets_file)
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
        importer['extensions'] += 1

        k += 1
        if LIMIT and k >= LIMIT:
            break

    # Set up the CSV headers (assume first extension is like all others)
    if write_csv_file:
        print('Writing CSV file...')
        fieldnames = exts[0].details.keys()
        csv_outfile = open('chrome-webstore-details.csv', 'w', newline='')
        writer = csv.DictWriter(csv_outfile, delimiter=',', fieldnames=fieldnames,
                                restval='', quoting=csv.QUOTE_ALL)
        writer.writeheader()

    for ext in exts:
        if ext.details and ext.details['Users']:
            # Do a little cleanup on users to make the CSV easier to manipulate
            users = ext.details['Users'].split()[0]
            users = users.replace(',', '')
            ext.details['Users'] = int(users.replace('+', ''))

        if ext.missing['apis']:
            importer['missing_apis'] += 1
            apis_counter.update(ext.missing['apis'])
            ext.details['Missing API'].extend(ext.missing['apis'])

        if ext.missing['permissions']:
            importer['missing_permissions'] += 1
            permissions_counter.update(ext.missing['permissions'])
            ext.details['Missing Permissions'].extend(ext.missing['permissions'])

        if ext.missing['manifests']:
            importer['missing_manifests'] += 1
            manifests_counter.update(ext.missing['manifests'])
            ext.details['Missing Manifest Keys'].extend(ext.missing['manifests'])

        if (not ext.missing['permissions']
            and not ext.missing['apis']
            and not ext.missing['manifests']):
            importer['easy_conversion'] += 1
            ext.details['Portable'] = 'Yes'

        if ext.usesBrowserNS:
            importer['browser_namespace'] += 1

        if ext.no_apis:
            importer['no_apis'] += 1

        if write_csv_file:
            try:
                writer.writerow(ext.details)
            except:
                # Usually fails because of a charset issue
                print('Couldn\'t write row in CSV file')



    print('Importer stats')
    print('--------------')

    def display(k, divisor):
        v = importer[k]
        pct = (v / float(importer[divisor])) * 100
        print((' {:6d} {:3.2f}% {}'.format(v, pct, k)))

    display('total', 'total')
    display('extensions', 'total')
    display('apps', 'total')
    display('themes', 'total')
    display('error', 'total')
    print()
    display('missing_permissions', 'extensions')
    display('missing_apis', 'extensions')
    display('missing_manifests', 'extensions')
    print()
    display('easy_conversion', 'extensions')
    display('browser_namespace', 'extensions')
    display('no_apis', 'extensions')

    print()
    print('Chrome API coverage')
    print('-------------------')

    for size in [100, 250]:
        topTotal = topCovered = size
        for k, v in usage_counter.most_common(topTotal):
            if apis_counter[k] > 0:
                topCovered -= 1
        pct = (float(topCovered) / float(topTotal)) * 100
        print((' {:6d} {:3.2f}% top {} API'.format(topCovered, pct, topTotal)))

    ct = 0
    print()
    print('Top API usage')
    print('------------')
    for k, v in usage_counter.most_common(250):
        ct += 1
        if (apis_counter[k] > 0):
            need = '-'
        else:
            need = '+'
        print(' {:3d}'.format(ct), ' {:6d} {} {}'.format(v, need, k))

    print()
    print('Missing APIs')
    print('------------')
    for k, v in apis_counter.most_common(100):
        print((' {:6d} {}'.format(v, k)))

    print()
    print('Missing permissions')
    print('-------------------')
    for k, v in permissions_counter.most_common(100):
        print((' {:6d} {}'.format(v, k)))

    print()
    print('Missing manifests')
    print('-------------------')
    for k, v in manifests_counter.most_common(100):
        print((' {:6d} {}'.format(v, k)))

    if False: #custom_counter:
        print()
        print('Custom counter')
        print('--------------')
        for k, v in sorted(custom_counter.most_common(100)):
            if isinstance(v, list):
                avg = sum([len(i) for i in v])/len(v)
                print((' {:6d} {} average'.format(avg, k)))
                v = len(v)

            print((' {:6d} {}'.format(v, k)))

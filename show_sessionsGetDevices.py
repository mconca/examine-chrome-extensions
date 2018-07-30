import codecs
from collections import Counter
import json
import pprint
import os

# Max number of addons to parse, None is all of them.
#LIMIT = 5000
LIMIT = None

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


class Extension:

    def __init__(self, manifest_file, apis_file):
        self.type = 'extension'
        self.has_gd = False
        if not os.path.exists(apis_file):
            raise ValueError('Missing API file')

        self.manifest_filename = manifest_file

        data = codecs.open(manifest_file, 'r', 'utf-8-sig').read()
        self.manifest = json.loads(data)
        data = codecs.open(apis_file, 'r', 'utf-8-sig').read()
        self.apis = json.loads(data)

        # Examine the apis
        for api in self.apis:
            if api.endswith('sessions.getDevices'):
                self.has_gd = True
        
        if self.is_app():
            self.type = 'app'

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



if __name__=='__main__':
    k = e = a = 0
    print('Extensions using sessions.getDevices() on CWS')
    print('---------------------')
    for filename in os.listdir('extensions/chrome-manifests'):
        if not filename.endswith('.json'):
            continue

        full = os.path.abspath(
            os.path.join('extensions/chrome-manifests', filename))
        apis_file = full.replace('chrome-manifests', 'chrome-apis')

        # Filter out ones that fail to import.
        try:
            ext = Extension(full, apis_file)
        except ValueError:
            continue

        if ext.has_gd:
            if ext.type == 'app':
                a += 1
            elif ext.type == 'extension':
                e += 1
            dets_file = full.replace('chrome-manifests', 'chrome-details')
            data = codecs.open(dets_file, 'r', 'utf-8-sig').read()
            res = json.loads(data)
            if not res['Name']:
                res['Name'] = '??????????'
            try:
                print(res['Name'] + ', ' + ext.type + ',', res['Users'])
            except:
                print('??????????, ' + ext.type + ',', res['Users'])

        k += 1
        if LIMIT and k >= LIMIT:
            break

    print('Extensions:%d   Apps:%d', e, a)

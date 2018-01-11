import json
import os
import requests
import sys

root = os.path.join(os.path.abspath(os.curdir), 'extensions')
amo_server = 'https://addons.mozilla.org'
out_file = 'firefox-urls.json'
firefox_detail_fields = {
    'Name' : ['name', 'en-US'],    # only grabs US english names, ugh...
    'Users' : ['average_daily_users'],
    'Rating' : ['ratings', 'average'],
    'Num Ratings' : ['ratings', 'count'],
    'Developer' : ['authors', 0, 'username']
}

results = set()
sys.setrecursionlimit(200000)

def fetch(url=None):
    url = url or amo_server + '/api/v3/addons/search/?sort=created&type=extension'
    print('Fetching: {}'.format(url))
    res = requests.get(url)
    res.raise_for_status()

    res_json = res.json()
    for addon in res_json['results']:
        current = addon['current_version']

        # An extension can have multiple files, but it always seems
        # to be a file per OS.  Let's just use the first file
        # so, later, we don't overcount the APIs used in an extension.
        file_obj = current['files'][0]
#        for file_obj in current['files']:
        if file_obj['is_webextension']:

            # Record URL to extension
            results.add(file_obj['url'])

            # Store off some details
            id = str(file_obj['id'])
            json_file = os.path.join(root, 'firefox-details', id + '.json')
            if (os.path.exists(json_file)):
                print('Details %s already exists, skipping' % id)
                continue

            res = {}
            for field, path in firefox_detail_fields.items():
                add_copy = addon
                try:
                    for k in path:
                        add_copy = add_copy[k]
                    val = add_copy
                except:
                    val = ''
                res[field] = val

            json.dump(res, open(json_file, 'w'))
            print('Got details for', id)

    if res_json['next']:
        fetch(res_json['next'])


if __name__=='__main__':
    fetch()
    json.dump(sorted(list(results)),open(out_file,'w'), indent=2, sort_keys=True)

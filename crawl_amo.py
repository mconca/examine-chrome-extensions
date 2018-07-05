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

try:
    results = set(json.load(open(outfile)))
    print('Loaded %d URLs', len(results))
except:
    results = set()
sys.setrecursionlimit(200000)

def fetch(sortOrder, url=None):

    # Leave the sort parametere, it seems to prevent duplicate results from being returned.
    url = url or (amo_server + '/api/v4/addons/search/?type=extension&page_size=50&app=firefox&sort=' + sortOrder)
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
        fetch(sortOrder, res_json['next'])


if __name__=='__main__':
    # We run the query twice because AMO has an arbitrary limit of 25,000 results from
    # a search query. So by querying the top 25K by users and top 25K by last date
    # updated, I get the most popular extensions, as well as the most recent.
    fetch('users')
    fetch('updated')
    json.dump(sorted(list(results)),open(out_file,'w'), indent=2, sort_keys=True)
    print('Output %d URLs', len(results))

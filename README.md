Installation
------------

    git clone https://github.com/mconca/chrome-extensions-archive
    cd examine-chrome-extensions
    pip install -r requirements.txt

Examining extensions on Chrome Web Store
--------------------------

Please note this requires Python 3.

Within the chrome-extensions-archive repo run:

    python3 crawl_sitemap.py.

The URL of all Chrome extensions are stored in crawled/sitemap/result.json

Copy this file over to the examine-chrome-extensions repo directory as chrome-urls.json

Then run:

    python get_manifest_and_json.py chrome

This will download each referenced file, extract the manifest.json and then do a naive grep for all references to chrome.* in the extension.

Then finally run:

    python parse_manifest_and_json.py

You should get some text output on the terminal screen, as well as a CSV file with extension details.

Examining extensions on AMO
--------------------------

Please note this requires Python 3.

In the examine-chrome-extensions repo directory, run

    python crawl_amo.py
    python get_manifest_and_json.py firefox

This will download each referenced file and extract the manifest.json.

Then finally run:

    python parse_firefox_apis.py

You should get some text output on the terminal screen, as well as a CSV file with extension details.


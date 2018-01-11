Installation
------------

    git clone https://github.com/andymckay/examine-chrome-extensions
    cd examine-chrome-extensions
    pip install -r requirements.txt

Examine lots of extensions
--------------------------

To get the list in results.json, use this project.:

    https://github.com/mdamien/chrome-extensions-archive

Please note this requires Python 3. Then run:

    python3 crawl_sitemap.py.

Copy the resulting data over to result.json.

To get the list in schemas.json, use this project:

    http://github.com/andymckay/arewewebextensionsyet.com

And run:

    python generate.py schemas-only

Copy the result data over to schema.json

Then run:

    python parse_manifest_and_json.py

This will download each referenced file, extract the manifest.json and then do a naive grep for all references to chrome.* in the extension.

Then finally run:

    python parse_manifest_and_json.py

And you should get some output.

Examine just one extension
--------------------------

Will grab extension from the Chrome store, unpack it and see what it's missing:

    python parse_extension.py https://chrome.google.com/webstore/detail/adblock-for-youtube/cmedhionkhpnakcndndgjdbohmhepckk/
    Manifest keys missing
      optional_permissions
    Try the add-on using:
      web-ext run -v -s /var/folders/h5/cbsbsk_j0f984db_n771zwz00000gn/T/tmpyop_kj

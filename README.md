To get the list in results.json, use this project:

https://github.com/mdamien/chrome-extensions-archive

And run, crawl_sitemap.py.

Copy the resulting data over to result.json.

To get the list in schemas.json, use this project:

http://github.com/andymckay/arewewebextensionsyet.com

And run, generate.py schemas-only.

Copy the result data over to schema.json

Then run:

python parse_manifest_and_json.py

This will download each referenced file, extract the manifest.json and then do a naive grep for all references to chrome.* in the extension.

Then finally run:

python parse_manifest_and_json.py

And you should get some output.

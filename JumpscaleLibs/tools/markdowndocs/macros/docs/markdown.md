# Markdown macro
Use this macro to include mardown text from a google doc into your docsite.


## Prerequisites

The macro uses google service account credentials.

### Service account
- Create project using [Google console](https://console.developers.google.com/flows/enableapi?apiid=slides.googleapis.com) and enable Google Drive API.
- Create credentials (type service account)
- Download credentials (as json and save it anywhere on your filesystem) then add move it to /sandbox/var/cred.json

## Use the macro in your markdown doc:
```
!!!markdown
https://docs.google.com/document/d/1h8fydUhQ1HTlt1zabbF9pJM1JHGkI_-58BygtsyWy0c/edit

```

the macro reads plain text from the google doc, so the text should be in a proper markdown format.

## Load your docsite:

Run the wiki package `kosmos -p 'j.threebot.package.wikis.start()'`

Then load your docsite.

```
url = "url in github that have your md file"
doc = j.tools.markdowndocs.load(url, name="doc")
doc.write()

 ```

open it at **localhost:80/wiki/doc**

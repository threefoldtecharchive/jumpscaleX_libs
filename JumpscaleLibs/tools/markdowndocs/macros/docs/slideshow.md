# Slideshow macro 
you can use this macro to include slides from different presentations into your docsite

# Prerequisites 
In order to use this macro you must make sure that Gdrive package is working, check the
[docs here](https://github.com/threefoldtech/digitalmeX/blob/master/packages/gdrive/README.md)
The macro uses google service account credentials.

### Service account
- Create project using [Google console](https://console.developers.google.com/flows/enableapi?apiid=slides.googleapis.com) and enable Google Drive API.
- Create credentials (type service account)
- Download credentials (as json and save it anywhere on your filesystem) then add move it to /sandbox/var/cred.json

### Example

```
!!!slideshow
presentation_1 = {presentation_guid}
presentation_2 = {presentation_guid}

slide_1 = presentation_1[{slide_name_or_guid}]
slide_2 = presentation_2[{slide_name_or_guid}]
```

Note: You can use "one slide fragment" unlimited times but if u want to use "multiple slides fragment" you are only allowed to use one time per page.

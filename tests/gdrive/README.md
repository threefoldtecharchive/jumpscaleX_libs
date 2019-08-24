#### Before running this test:

1- Install requirement `pip3 install -r requirements.txt`.

2- Google credential file should be added to current directory under name `cred.json`.

3- Add endpoints need to be tested in `pdf_links.txt`, `png_links.txt`.

#### To run test:
```bash
nosetests-3.4 -v testcases.py
```

#### Before running this test:

1- Install requirement `pip3 install -r requirements.txt`.

2- Create Gdrive client instance `main` with the right Google credential `info` should be created.

3- Add endpoints need to be tested in `pdf_links.txt`, `png_links.txt`.

#### To run test:
```bash
nosetests-3.4 -v testcases.py
```

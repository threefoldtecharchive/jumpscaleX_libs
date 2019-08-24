from .basetest import Basetest
from parameterized import parameterized
import requests

with open("png_links.txt", "r") as f:
    png_links = f.readlines()

with open("pdf_links.txt", "r") as f:
    pdf_links = f.readlines()

png_urls = list()
pdf_urls = list()
[png_urls.append(i.strip("\n")) for i in png_links if i not in ["\n", ""]]
[pdf_urls.append(i.strip("\n")) for i in pdf_links if i not in ["\n", ""]]


class Testcases(Basetest):
    @parameterized.expand(png_urls)
    def test001_png_urls(self, url):
        """ gslide-001 check urls contents are png.

        **Test Scenario:**

        #. Get request to a url.
        #. Check that url exists.
        #. Check that the content type is png.
        """
        self.log("Get request to url {}".format(url))
        req = requests.get(url)

        self.log("Check that url exists")
        self.assertEqual(req.status_code, requests.codes.ok, "Couldn't find this url")

        self.log("Check that the content type is png")
        content_type = req.headers["content-Type"]
        self.assertEqual(content_type, "image/png", "This url is not contains a png")

    @parameterized.expand(pdf_urls)
    def test002_pdf_urls(self, url):
        """ gslide-002 check urls contents are pdf.

        **Test Scenario:**

        #. Get request to a url.
        #. Check that url exists.
        #. Check that the content type is pdf.
        """
        self.log("Get request to a url {}".format(url))
        req = requests.get(url)

        self.log("Check that url exists")
        self.assertEqual(req.status_code, requests.codes.ok, "Couldn't find this url")

        self.log("Check that the content type is pdf")
        content_type = req.headers["content-Type"]
        self.assertEqual(content_type, "application/pdf", "This url is not contains a pdf")

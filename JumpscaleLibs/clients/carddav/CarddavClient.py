#!/usr/bin/env python
# vim: set ts=4 sw=4 expandtab sts=4:
# Copyright (c) 2011-2013 Christian Geier & contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# -------------------------------------------------------------------------------
# Lukasz Janyst:
#
# lxml encoding issue:
# * Remove '<?xml version="1.0" encoding="utf-8"?>' header from responses
#   to prevent etree errors
#
# requests-0.8.2:
# * Remove the verify ssl flag - caused exception
# * Add own raise_for_status for more meaningful error messages
# * Fix digest auth
# -------------------------------------------------------------------------------

"""
contains the class PyCardDAV and some associated functions and definitions
"""
from Jumpscale import j
from collections import namedtuple
import requests
import sys
from urllib.parse import urlparse, urljoin
import logging
import lxml.etree as ET
import string

JSConfigClient = j.baseclasses.object_config


def raise_for_status(resp):
    if 400 <= resp.status_code < 500 or 500 <= resp.status_code < 600:
        msg = "Error code: " + str(resp.status_code) + "\n"
        msg += resp.content
        raise requests.exceptions.HTTPError(msg)


def get_random_href():
    """returns a random href"""
    import random

    tmp_list = list()
    for _ in range(3):
        rand_number = random.randint(0, 0x100000000)
        tmp_list.append("{0:x}".format(rand_number))
    return "-".join(tmp_list).upper()


DAVICAL = "davical"
SABREDAV = "sabredav"
UNKNOWN = "unknown server"


class UploadFailed(Exception):
    """uploading the card failed"""

    pass

class CarddavClient(JSConfigClient):
    """class for interacting with a CardDAV server

    Since PyCardDAV relies heavily on Requests [1] its SSL verification is also
    shared by PyCardDAV [2]. For now, only the *verify* keyword is exposed
    through PyCardDAV.

    [1] http://docs.python-requests.org/
    [2] http://docs.python-requests.org/en/latest/user/advanced/

    raises:
        requests.exceptions.SSLError
        requests.exceptions.ConnectionError
        more requests.exceptions depending on the actual error
        Exception (shame on me)

    """

    _SCHEMATEXT = """
    @url = jumpscale.carddav.client.1
    resource = "" (S)
    user = "" (S)
    passwd = "" (S)
    """

    def _init(self, debug="", verify=True, write_support=False, auth="basic", **kwargs):
        # shutup url3
        urllog = logging.getLogger("requests.packages.urllib3.connectionpool")
        urllog.setLevel(logging.CRITICAL)
        self.user = self.user
        split_url = urlparse(self.resource)
        url_tuple = namedtuple("url", "resource base path")
        self.url = url_tuple(self.resource, split_url.scheme + "://" + split_url.netloc, split_url.path)
        self.debug = debug
        self.session = requests.session()
        self.write_support = write_support
        self._settings = {"verify": verify}
        if auth == "basic":
            self._settings["auth"] = (self.user, self.passwd)
        if auth == "digest":
            from requests.auth import HTTPDigestAuth

            self._settings["auth"] = HTTPDigestAuth(self.user, self.passwd)
        self._default_headers = {"User-Agent": "pyCardDAV"}
        response = self.session.request("PROPFIND", self.resource, headers=self.headers, **self._settings)
        raise_for_status(response)  # raises error on not 2XX HTTP status code

    @property
    def verify(self):
        """gets verify from settings dict"""
        return self._settings["verify"]


    @property
    def headers(self):
        return dict(self._default_headers)

    def _check_write_support(self):
        """checks if user really wants his data destroyed"""
        if not self.write_support:
            sys.stderr.write("Sorry, no write support for you. Please check " "the documentation.\n")
            sys.exit(1)

    def delete_abook(self, href, etag=None):
        remotepath = str(self.url.base + href)
        headers = self.headers
        headers["content-type"] = "text/vcard"
        if etag is not None:
            headers["If-Match"] = etag
        result = self.session.delete(remotepath, headers=headers, **self._settings)
        raise_for_status(result)

    def create_abook(self, name, description, href):
        url = urljoin(self.url.base, self.user + "/")
        if not href:
            href = get_random_href()
        url = urljoin(url, href)
        self.session.request(
            "MKCOL",
            url,
            data=f"""\
<?xml version="1.0" encoding="UTF-8" ?>
<create
        xmlns="DAV:"
        xmlns:C="urn:ietf:params:xml:ns:caldav"
        xmlns:CR="urn:ietf:params:xml:ns:carddav"
        xmlns:I="http://apple.com/ns/ical/"
        xmlns:INF="http://inf-it.com/ns/ab/">
        <set>
                <prop>
                        <resourcetype>
                                <collection />
                                <CR:addressbook />
                        </resourcetype>
                        <displayname>{name}</displayname>
                        <INF:addressbook-color>#ba4a53ff</INF:addressbook-color>
                        <CR:addressbook-description>{description}</CR:addressbook-description>
                </prop>
        </set>
</create>
""".encode(
                "utf-8"
            ),
        )

    def _detect_server(self):
        """detects CardDAV server type

        currently supports davical and sabredav (same as owncloud)
        :rtype: string "davical" or "sabredav"
        """
        response = requests.request("OPTIONS", self.url.base, headers=self.headers)
        if "X-Sabre-Version" in response.headers:
            server = SABREDAV
        elif "X-DAViCal-Version" in response.headers:
            server = DAVICAL
        else:
            server = UNKNOWN
        logging.info(server + " detected")
        return server

    def get_abook(self, href=None):
        """does the propfind and processes what it returns

        :rtype: list of hrefs to vcards
        """
        xml = self._get_xml_props(href=href)
        abook = self._process_xml_props(xml)
        return abook

    def find_vcard(self, text, abook_href=None):
        matched = []
        for vcard_href in self.get_abook(href=abook_href):
            if self.get_vcard(vcard_href).find(text):
                matched.append(vcard_href)
        return matched

    def get_vcard(self, href):
        """
        pulls vcard from server

        :returns: vcard
        :rtype: string
        """
        response = self.session.get(self.url.base + href, headers=self.headers, **self._settings)
        raise_for_status(response)
        return response.content

    def update_vcard(self, card, href, etag):
        """
        pushes changed vcard to the server
        card: vcard as unicode string
        etag: str or None, if this is set to a string, card is only updated if
              remote etag matches. If etag = None the update is forced anyway
         """
        # TODO what happens if etag does not match?
        self._check_write_support()
        remotepath = str(self.url.base + href)
        headers = self.headers
        headers["content-type"] = "text/vcard"
        if etag is not None:
            headers["If-Match"] = etag
        self.session.put(remotepath, data=card.encode("utf-8"), headers=headers, **self._settings)

    def delete_vcard(self, href, etag):
        """deletes vcard from server

        deletes the resource at href if etag matches,
        if etag=None delete anyway
        :param href: href of card to be deleted
        :type href: str()
        :param etag: etag of that card, if None card is always deleted
        :type href: str()
        :returns: nothing
        """
        # TODO: what happens if etag does not match, url does not exist etc ?
        self._check_write_support()
        remotepath = str(self.url.base + href)
        headers = self.headers
        headers["content-type"] = "text/vcard"
        if etag is not None:
            headers["If-Match"] = etag
        result = self.session.delete(remotepath, headers=headers, **self._settings)
        raise_for_status(result)

    def upload_new_card(self, card, abook_href=None):
        """
        upload new card to the server

        :param card: vcard to be uploaded
        :type card: unicode
        :rtype: tuple of string (path of the vcard on the server) and etag of
                new card (string or None)
        """
        url = urljoin(self.url.base, abook_href) if abook_href else self.url.resource
        self._check_write_support()
        card = card.encode("utf-8")
        for _ in range(0, 5):
            rand_string = get_random_href()
            remotepath = urljoin(url, rand_string + ".vcf")
            headers = self.headers
            headers["content-type"] = "text/vcard"
            headers["If-None-Match"] = "*"
            response = requests.put(remotepath, data=card, headers=headers, **self._settings)
            if response.ok:
                parsed_url = urlparse(remotepath)

                if "etag" not in response.headers:
                    etag = ""
                else:
                    etag = response.headers["etag"]

                return (parsed_url.path, etag)
        raise_for_status(response)

    def list_abooks(self):
        """PROPFIND method

        gets the xml file with all vcard hrefs

        :rtype: str() (an xml file)
        """
        headers = self.headers
        headers["Depth"] = "1"
        response = self.session.request(
            "PROPFIND", "{url}/{user}/".format(url=self.url.base, user=self.user), headers=headers, **self._settings
        )
        raise_for_status(response)
        if response.headers["DAV"].count("addressbook") == 0:
            raise Exception("URL is not a CardDAV resource")
        books = self._process_xml_props(response.content)
        return books

    def _get_xml_props(self, href=None):
        """PROPFIND method

        gets the xml file with all vcard hrefs

        :rtype: str() (an xml file)
        """
        headers = self.headers
        headers["Depth"] = "1"
        url = urljoin(self.url.base, href) if href else self.url.resource
        response = self.session.request("PROPFIND", url, headers=headers, **self._settings)
        raise_for_status(response)
        if response.headers["DAV"].count("addressbook") == 0:
            raise Exception("URL is not a CardDAV resource")

        return response.content

    @classmethod
    def _process_xml_props(cls, xml):
        """processes the xml from PROPFIND, listing all vcard hrefs

        :param xml: the xml file
        :type xml: str()
        :rtype: dict() key: href, value: etag
        """
        xml = xml.replace(b'<?xml version="1.0" encoding="utf-8"?>', b"", 1)
        namespace = "{DAV:}"

        element = ET.XML(xml)
        abook = dict()
        for response in element.iterchildren():
            if response.tag == namespace + "response":
                href = ""
                etag = ""
                insert = False
                for refprop in response.iterchildren():
                    if refprop.tag == namespace + "href":
                        href = refprop.text
                        # if not href.endswith(".vcf"):
                        #     break
                    for prop in refprop.iterchildren():
                        for props in prop.iterchildren():
                            if props.tag == namespace + "getcontenttype" and (
                                props.text == "text/vcard"
                                or props.text == "text/vcard;charset=utf-8"
                                or props.text == "text/x-vcard"
                                or props.text == "text/x-vcard;charset=utf-8"
                            ):
                                insert = True
                            if props.tag == namespace + "getetag":
                                etag = props.text
                        if insert:
                            abook[href] = etag
        return abook

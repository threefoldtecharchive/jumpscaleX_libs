from Jumpscale import j

JSBASE = j.baseclasses.object


class LegalContractsFactory(j.baseclasses.object):
    # check https://github.com/threefoldtech/jumpscaleX_libs/issues/new
    def install(self):
        # p = j.tools.prefab.local
        j.tools.reportlab.install()

    def doc_get(self, path):
        from .LegalDoc import LegalDoc

        return LegalDoc(path)

    def test(self, install=False):
        """
        kosmos 'j.tools.legal_contracts.test(install=False)'

        :return:
        """
        if install:
            self.install()

        testdir = "/tmp/legaldocs/"
        j.sal.fs.createDir(testdir)

        path = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldfoundation/info_legal/tree/master/HR/dutch"
        )
        logo_path = j.clients.git.getContentPathFromURLorPath(
            "https://github.com/threefoldfoundation/info_legal/tree/master/images/threefold_logo.png"
        )

        doc = self.doc_get("%s/test_legal.pdf" % testdir)

        j.shell()
        w

        p = j.tools.prefab.local
        url = "https://media.wired.com/photos/598e35994ab8482c0d6946e0/master/w_628,c_limit/phonepicutres-TA.jpg"

        j.shell()

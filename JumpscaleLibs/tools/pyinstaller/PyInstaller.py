from Jumpscale import j
import imp

JSBASE = j.baseclasses.object


class PyInstaller(j.baseclasses.object):
    """
    """

    __jslocation__ = "j.tools.pyinstaller"

    def _init(self, **kwargs):
        pass

    def install(self):
        """
        kosmos 'j.tools.pyinstaller.install()'
        :return:
        """

        j.shell()

    def build_jsx(self):
        j.shell()

from Jumpscale import j

JSBASE = j.baseclasses.object

import time
import inspect
import sys

import pyximport

JSBASE = j.baseclasses.object


class CythonFactory(j.baseclasses.object):
    """
    example:
        '''
        j.core.cython.addCodePath("/tmp")
        #there need to be a helloworld.pyx in that path
        import helloworld
        helloworld.echo()
        '''
    """

    __jslocation__ = "j.tools.cython"

    def _init(self, **kwargs):
        self.__imports__ = "cython"
        self.__path = ""
        self._currentPath

    @property
    def _currentPath(self):
        if self.__path == "":
            self.__path = j.sal.fs.getDirName(inspect.getsourcefile(self.__init__))
            sys.path.append(self.__path)
            pyximport.install()
        return self.__path

    def addCodePath(self, path):
        if path not in sys.path:
            sys.path.append(path)

    def test(self):
        import helloworld

        helloworld.echo()
        # helloworld.spam(10, bytearray("this is a test: int:\n".encode()))
        # helloworld.spam(10, b"this is a test: int:\n")

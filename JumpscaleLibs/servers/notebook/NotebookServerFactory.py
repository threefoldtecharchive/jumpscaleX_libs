from Jumpscale import j


skip = j.baseclasses.testtools._skip


class NotebookServerFactory(j.baseclasses.object):

    __jslocation__ = "j.servers.notebook"

    def install(self):
        j.builders.system.package.update()
        j.builders.system.package.install("nodejs")
        j.builders.system.package.install("npm")

        try:
            import jupyterlab
        except:
            j.builders.runtimes.python3.pip_package_install("prompt-toolkit", reset=True)
            j.builders.runtimes.python3.pip_package_install(
                "jupyterlab,notebook,voila,bqplot,pandas,beakerx", reset=True
            )
            # make sure the prompt toolkit stays below 3
            j.builders.runtimes.python3.pip_package_install("prompt-toolkit<3.0.0", reset=True)
            j.sal.process.execute("jupyter labextension install @jupyter-widgets/jupyterlab-manager bqplot")

    def start(
        self,
        path="{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks/threefold_simulator.ipynb",
        background=False,
        voila=False,
    ):
        """
        kosmos 'j.servers.notebook.start()'
        kosmos 'j.servers.notebook.start(voila=True)'
        """
        self.install()
        path = j.core.tools.text_replace(path)
        dirpath = j.sal.fs.getDirName(path)
        basepath = j.sal.fs.getBaseName(path)
        self._log_info(path)
        if not background:
            if not voila:
                cmd_start = "cd %s;jupyter lab --ip=0.0.0.0 --allow-root %s" % (dirpath, basepath)
                j.sal.process.executeInteractive(cmd_start)
            else:
                cmd_start = "cd %s;voila %s" % (dirpath, basepath)
                j.sal.process.executeInteractive(cmd_start)
        else:
            if not voila:
                cmd_start = "jupyter lab --ip=0.0.0.0 --allow-root %s" % path
                cmd = j.servers.startupcmd.get("notebook", cmd_start=cmd_start)
                cmd.start()
            else:
                cmd_start = "voila %s" % (path)
                cmd = j.servers.startupcmd.get("voila", cmd_start=cmd_start)
                cmd.start()

            url = "http://172.17.0.2:8888/?token=6a2d48493cf72c098135dc5fa0ea4f318d9e7185ca30b1fb"
            # TODO: need to show url where to go to

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/105")
    def test(self):
        """
        kosmos 'j.servers.notebook.test()'
        :return:
        """
        self.start(True)

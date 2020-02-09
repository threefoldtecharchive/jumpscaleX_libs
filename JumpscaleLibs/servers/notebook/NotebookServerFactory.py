from Jumpscale import j


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

        j.shell()

    def start(
        self,
        path="{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks",
        background=True,
    ):
        self.install()

        cmd = "jupyter lab --ip=0.0.0.0 --no-browser --allow-root"

        url = "http://172.17.0.2:8888/?token=6a2d48493cf72c098135dc5fa0ea4f318d9e7185ca30b1fb"
        pass

    def test(self):
        """
        kosmos 'j.servers.notebook.test()'
        :return:
        """
        self.start(True)

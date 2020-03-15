from Jumpscale import j

skip = j.baseclasses.testtools._skip

import gevent


class NotebookServerFactory(j.baseclasses.object):

    __jslocation__ = "j.servers.notebook"

    def install(self):
        """
        kosmos -p 'j.servers.notebook.install()'
        """
        j.builders.system.package.update()
        j.builders.runtimes.nodejs.install()

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
        base_url=None,
        ip="0.0.0.0",
    ):
        """
        kosmos 'j.servers.notebook.start()'
        kosmos 'j.servers.notebook.start(voila=True)'
        """
        path = j.core.tools.text_replace(path)
        dirpath = j.sal.fs.getDirName(path)
        basepath = j.sal.fs.getBaseName(path)
        self._log_info(path)
        if not background:
            if not voila:
                cmd_start = (
                    "cd %s;jupyter lab --NotebookApp.allow_remote_access=True --NotebookApp.token='' --NotebookApp.password='' --ip=%s --allow-root %s"
                    % (dirpath, ip, basepath)
                )
                if base_url:
                    cmd_start += f" --NotebookApp.base_url={base_url}"

                j.sal.process.executeInteractive(cmd_start)

            else:
                cmd_start = "cd %s;voila --Voila.ip=%s %s" % (dirpath, ip, basepath)
                if base_url:
                    cmd_start += f" --Voila.base_url={base_url}"

                j.sal.process.executeInteractive(cmd_start)
        else:
            if not voila:
                cmd_start = (
                    "jupyter lab --NotebookApp.allow_remote_access=True --NotebookApp.token='' --NotebookApp.password='' --ip=%s --allow-root %s"
                    % (ip, path)
                )
                if base_url:
                    cmd_start += f" --NotebookApp.base_url={base_url}"
                cmd = j.servers.startupcmd.get("notebook", cmd_start=cmd_start)
                cmd.start()
            else:
                cmd_start = "voila --Voila.ip=%s %s" % (ip, path)
                if base_url:
                    cmd_start += f" --Voila.base_url={base_url}"
                cmd = j.servers.startupcmd.get("voila", cmd_start=cmd_start)
                cmd.start()

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/105")
    def test(self):
        """
        kosmos 'j.servers.notebook.test()'
        :return:
        """
        self.start(True)

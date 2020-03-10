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
        j.builders.system.package.install("nodejs")
        j.builders.system.package.install("npm")

        try:
            import jupyterlab
        except:
            j.builders.runtimes.python3.pip_package_install("prompt-toolkit", reset=True)
            j.builders.runtimes.python3.pip_package_install("jupyterlab,notebook,voila", reset=True)
            # ,bqplot,pandas,beakerx,matplotlib
            # make sure the prompt toolkit stays below 3
            j.builders.runtimes.python3.pip_package_install("prompt-toolkit<3.0.0", reset=True)
            # j.sal.process.execute("jupyter labextension install @jupyter-widgets/jupyterlab-manager bqplot")
            j.sal.process.execute("jupyter labextension install plotlywidget")
            j.sal.process.execute("jupyter notebook --generate-config")

    def start(
        self,
        path="{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks/nodebatch_simulator.ipynb",
        background=False,
        voila=False,
        base_url=None,
        ip="0.0.0.0",
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
                # cmd_start = "cd %s;jupyter lab --ip=0.0.0.0 --allow-root %s" % (dirpath, basepath)
                cmd_start = "cd %s;jupyter notebook --ip=0.0.0.0 --allow-root %s" % (dirpath, basepath)
                # cmd_start = (
                #     "cd %s;jupyter lab --NotebookApp.allow_remote_access=True --NotebookApp.token='' --NotebookApp.password='' --ip=%s --allow-root %s"
                #     % (dirpath, ip, basepath)
                # )
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
                # cmd_start = "jupyter lab --ip=0.0.0.0 --allow-root %s" % path
                cmd_start = "jupyter notebook --ip=0.0.0.0 --allow-root %s" % path
                # cmd_start = (
                #     "jupyter lab --NotebookApp.allow_remote_access=True --NotebookApp.token='' --NotebookApp.password='' --ip=%s --allow-root %s"
                #     % (ip, path,)
                # )
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

        # if j.core.platformtype.myplatform.platform_is_linux:
        #     j.sal.process.execute(
        #         f"""sed -i "/c.NotebookApp.notebook_dir/c\c.NotebookApp.notebook_dir = '{path}'" ~/.jupyter/jupyter_notebook_config.py"""
        #     )
        #
        # cmd = "source /sandbox/env.sh && jupyter lab --ip=0.0.0.0 --no-browser --allow-root"
        # j.sal.process.execute(cmd)
        # url = "http://172.17.0.2:8888/?token=6a2d48493cf72c098135dc5fa0ea4f318d9e7185ca30b1fb"
        # pass
        # # url = "http://172.17.0.2:8888/?token=6a2d48493cf72c098135dc5fa0ea4f318d9e7185ca30b1fb"
        # # TODO: need to show url where to go to

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/105")
    def test(self):
        """
        kosmos 'j.servers.notebook.test()'
        :return:
        """
        self.start(True)

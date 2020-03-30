from Jumpscale import j

skip = j.baseclasses.testtools._skip


class NotebookServerFactory(j.baseclasses.object):

    __jslocation__ = "j.servers.notebook"

    def install(self, force=False):
        """
        kosmos 'j.servers.notebook.install(force=True)'

        """

        try:
            import jupyterlab
        except:
            force = True

        if force:

            j.builders.system.package.update()

            if j.core.myenv.platform_is_linux:
                C = """
                sudo curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash
                apt-get install -y nodejs
                """
                j.core.tools.execute(C)
            else:
                j.builders.runtimes.nodejs.install()

            j.builders.runtimes.python3.pip_package_install("prompt-toolkit", reset=True)
            j.builders.runtimes.python3.pip_package_install(
                "jupyterlab,notebook,voila,plotly,pandas,jupyterlab_code_formatter,plotly,voila-gridstack,voila-vuetify,ipywidgets",
                reset=True,
            )
            # make sure the prompt toolkit stays below 3
            j.builders.runtimes.python3.pip_package_install("prompt-toolkit==2.0.9", reset=True)
            j.builders.runtimes.python3.pip_package_install("ptpython==2.0.4", reset=True)
            C = """
            export NODE_OPTIONS=--max-old-space-size=4096

            jupyter labextension install @jupyter-voila/jupyterlab-preview --no-build   
            jupyter labextension install @ryantam626/jupyterlab_code_formatter --no-build            
            jupyter labextension install @jupyter-widgets/jupyterlab-manager --no-build
            jupyter labextension install jupyterlab-plotly --no-build
            jupyter labextension install plotlywidget --no-build
            jupyter labextension install voila --no-build
            jupyter labextension install @krassowski/jupyterlab_go_to_definition --no-build 
                        
            jupyter lab build  --minimize=False
            
            jupyter extension enable voila --sys-prefix
            jupyter nbextension install voila --sys-prefix --py
            jupyter nbextension enable voila --sys-prefix --py            

            # jupyter serverextension enable --py jupyterlab_code_formatter
            # jupyter serverextension enable --py jupyterlab-manager
                        
            """
            j.core.tools.execute(C)

    def start(
        self,
        path="{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks/threefold_simulator.ipynb",
        background=False,
        voila=False,
        base_url=None,
        ip="0.0.0.0",
        port=80,
    ):
        """
        kosmos 'j.servers.notebook.start()'
        kosmos 'j.servers.notebook.start(voila=True)'
        """
        path = j.core.tools.text_replace(path)
        dirpath = j.sal.fs.getDirName(path)
        basepath = j.sal.fs.getBaseName(path)
        self.install()
        self._log_info(path)

        cmd = self.get_cmd(path=path, background=background, voila=voila, base_url=base_url, ip=ip, port=port)
        if not background:
            cmd = f"cd {dirpath};{cmd}"
            j.sal.process.executeInteractive(cmd)
        else:
            cmd = j.servers.startupcmd.get("notebook", cmd_start=cmd, path = dirpath)
            cmd.start()
        
    def get_cmd(self, 
        path=None,
        background=False,
        voila=False,
        base_url=None,
        ip="0.0.0.0",
        port=80):
        
        if not voila:
            cmd = "jupyter lab --NotebookApp.allow_remote_access=True --NotebookApp.token=''"
            cmd += f" --NotebookApp.password='' --ip={ip} --port={port} --allow-root"
        else:
            cmd = f"voila --Voila.ip={ip}  --Voila.port={80}"

        if base_url:
            cmd += f" --NotebookApp.base_url={base_url}"
        return cmd

    def stop(self,
        path="{DIR_CODE}/github/threefoldtech/jumpscaleX_libs_extra/JumpscaleLibsExtra/tools/threefold_simulation/notebooks/threefold_simulator.ipynb",
        background=False,
        voila=False,
        base_url=None,
        ip="0.0.0.0",
        port=80,):
        if background:
            cmd = self.get_cmd(path=path, background=background, voila=voila, base_url=base_url, ip=ip, port=port)
            cmd = j.servers.startupcmd.get("notebook", cmd_start=cmd)
            cmd.stop()
        else:
            raise Exception("Calling stop is not allowed if not running in background")
        

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/105")
    def test(self):
        """
        kosmos 'j.servers.notebook.test()'
        :return:
        """
        self.start(True)

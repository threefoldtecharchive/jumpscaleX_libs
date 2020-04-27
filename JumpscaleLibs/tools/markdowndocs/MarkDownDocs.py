from Jumpscale import j
from .DocSite import DocSite, Doc
import gevent
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import imp
import time
import sys

from .Link import Linker

JSBASE = j.baseclasses.object
TESTTOOLS = j.baseclasses.testtools
skip = j.baseclasses.testtools._skip


class Watcher:
    """
    a class to watch all dirs loaded in the docsite and reload it once changed
    """

    def __init__(self, docsites):
        print("initializing watcher for paths: {}".format(docsites))
        event_handler = DocsiteChangeHandler(self)
        self.docsites = docsites
        self.observer = PausingObserver()
        for _, docsite in docsites.items():
            self.observer.schedule(event_handler, docsite.path, recursive=True)

    def start(self):
        print("started watcher")
        self.observer.start()
        try:
            while True:
                gevent.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


class PausingObserver(Observer):
    def dispatch_events(self, *args, **kwargs):
        if not getattr(self, "_is_paused", False):
            super(PausingObserver, self).dispatch_events(*args, **kwargs)

    def pause(self):
        self._is_paused = True

    def resume(self):
        time.sleep(5)  # allow interim events to be queued
        self.event_queue.queue.clear()
        self._is_paused = False


class DocsiteChangeHandler(FileSystemEventHandler):
    def __init__(self, watcher):
        FileSystemEventHandler.__init__(self)
        self.watcher = watcher

    def on_modified(self, event):
        if event.is_directory or event.src_path.endswith(".swp"):
            return
        docsite = self.get_docsite_from_path(event.src_path)
        if docsite:
            site = j.tools.markdowndocs.load(docsite.path, docsite.name)
            self.watcher.observer.pause()
            site.write()
            self.watcher.observer.resume()

    def on_deleted(self, event):
        if event.src_path.endswith(".swp"):
            return
        docsite = self.get_docsite_from_path(event.src_path)
        file_dir = event.src_path.split(docsite.path)[1]
        if file_dir.startswith("/"):
            file_dir = file_dir[1:]
        file_dir = file_dir.lower()
        file_dir = j.sal.fs.joinPaths(docsite.outpath, file_dir)
        j.sal.fs.remove(file_dir)

    def get_docsite_from_path(self, path):
        for _, docsite in self.watcher.docsites.items():
            if docsite.path in path:
                return docsite


class MarkDownDocs(j.baseclasses.object, TESTTOOLS):
    """
    """

    __jslocation__ = "j.tools.markdowndocs"

    def _init(self, **kwargs):

        self.__imports__ = "toml"
        self._macroPathsDone = []
        self._initOK = False
        self._macroCodepath = j.sal.fs.joinPaths(j.dirs.VARDIR, "markdowndocs_internal", "macros.py")
        j.sal.fs.createDir(j.sal.fs.joinPaths(j.dirs.VARDIR, "markdowndocs_internal"))

        self.docsites = {}  # location in the outpath per site
        self.outpath = j.sal.fs.joinPaths(j.dirs.VARDIR, "markdowndocs")
        self._git_repos = {}
        self.defs = {}

        self._loaded = []  # don't double load a dir
        self._configs = []  # all found config files
        # self._macros_loaded = []

        self._macros_modules = {}  # key is the path
        self._macros = {}  # key is the name

        self._pointer_cache = {}  # so we don't have to full lookup all the time (for markdown docs)

        # lets make sure we have default macros
        self.macros_load()
        self._sonic_client = None

    def sonic_client_set(self, sonic_client):
        """
        set sonic client to be used to index docsites content
        :param sonic_client:
        :return:
        """
        self._sonic_client = sonic_client

    def _git_get(self, path):
        if path not in self._git_repos:
            try:
                gc = j.clients.git.get(path)
            except Exception as e:
                print("cannot load git:%s" % path)
                return
            self._git_repos[path] = gc
        return self._git_repos[path]

    # def _init(self,**kwargs):
    #     if not self._initOK:
    #         # self.install()
    #         j.clients.redis.core_get()
    #         j.sal.fs.remove(self._macroCodepath)
    #         # load the default macro's
    #         self.macros_load("https://github.com/Jumpscale/markdowndocs/tree/master/macros")
    #         self._initOK = True

    def macros_load(self, path_or_url=None):
        """
        @param path_or_url can be existing path or url
        """
        self._log_info("load macros:%s" % path_or_url)

        if not path_or_url:
            path_or_url = (
                "https://github.com/threefoldtech/jumpscaleX_libs/tree/*/JumpscaleLibs/tools/markdowndocs/macros"
            )

        path = j.clients.git.getContentPathFromURLorPath(path_or_url)

        if path not in self._macros_modules:

            if not j.sal.fs.exists(path=path):
                raise j.exceptions.Input("Cannot find path:'%s' for macro's, does it exist?" % path)

            for path0 in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.py", followSymlinks=True):
                name = j.sal.fs.getBaseName(path0)[:-3]  # find name, remove .py
                self._macros[name] = j.tools.jinja2.code_python_render(
                    obj_key=name, path=path0, reload=False, objForHash=name
                )
        # else:
        #     self._log_debug("macros not loaded, already there")

    def find_docs_path(self, path, base_path):
        """try to find docs path from base_path inside a given repo path and return it if exists

        :param path: repo path, e.g. `{DIR_BASE}/code/github/threefoldfoundation/info_foundation`
        :type path: str
        """
        gitpath = j.clients.git.findGitPath(path)
        if not gitpath or gitpath != path:
            return path

        docs_path = j.sal.fs.joinPaths(path, base_path)
        if j.sal.fs.exists(docs_path):
            return docs_path
        return path

    def load(self, path="", name="", base_path="docs", pull=False, download=False):
        self.macros_load()
        if path.startswith("http"):
            # check if we already have a git repo, then the current checked-out branch
            repo_args = j.clients.git.getGitRepoArgs(path)
            host = repo_args[0]
            dest = repo_args[-3]
            repo_dest = j.clients.git.findGitPath(dest, die=False)
            if repo_dest:
                # replace branch with current one
                current_branch = j.clients.git.getCurrentBranch(repo_dest)
                path = Linker.replace_branch(path, current_branch, host)
            path = self.find_docs_path(j.clients.git.getContentPathFromURLorPath(path, pull=pull), base_path)
        ds = DocSite(path=path, name=name)
        self.docsites[ds.name] = ds
        return self.docsites[ds.name]

    def reload(self, name):
        """Reload a wiki that was previously loaded

        :param name: wiki name
        :type name: str
        """
        docsite = DocSite.get_from_name(name)

        changed_files = []
        deleted_files = []

        # check for changed files in the repo dir
        repo = j.clients.git.get(docsite.path).repo
        for item in repo.index.diff(None):
            if item.change_type == "D":
                deleted_files.append(item.a_path)
            else:
                changed_files.append(item.a_path)

        # if no local changes, check the remote changes on github
        if not changed_files and not deleted_files:
            branch = repo.active_branch.name
            changed_files = repo.git.diff(f"origin/{branch}..HEAD", name_only=True, diff_filter=["AM"]).split("\n")
            deleted_files = repo.git.diff(f"origin/{branch}..HEAD", name_only=True, diff_filter=["D"]).split("\n")
            j.clients.git.pullGitRepo(dest=docsite.path, url=f"{docsite.metadata['repo']}")

        # remove unused files
        for ch_file in changed_files:
            if not ch_file.endswith(".md"):
                changed_files.remove(ch_file)

        def render_changes():
            """
            - get the wiki's docsite
            - for each changed file this will create a doc for it to write its changes
            """
            for ch_file in changed_files:
                file_name = j.sal.fs.getBaseName(ch_file).rstrip(".md")
                doc = Doc(name=file_name, path=f"{docsite.path}/{ch_file}", docsite=docsite)
                doc.path_dir_rel = ""
                doc.write()
                print(f"wiki: {docsite.name}, file: {ch_file}. Reloaded Successfuly")

            # clean up deleted files
            for del_file in deleted_files:
                if del_file != "":
                    file_name = j.sal.fs.getBaseName(del_file)
                    file_path = f"{docsite.outpath}/{file_name}"
                    if j.sal.bcdbfs.file_exists(file_path):
                        j.sal.bcdbfs.file_delete(file_path)
                        print(f"wiki: docsite.name, file: {del_file}. Deletion Success")

            print("Reload Success")

        render_changes()

    def git_update(self):
        if self.docsites == {}:
            self.load()
        for gc in self._git_repos:
            gc.pull()

    def item_get(self, name, namespace="", die=True, first=False):
        """
        """
        key = "%s_%s" % (namespace, name)

        import pudb

        pudb.set_trace()

        # we need the cache for performance reasons
        if not key in self._pointer_cache:

            # make sure we have the most dense ascii name for search
            ext = j.sal.fs.getFileExtension(name).lower()
            name = name[: -(len(ext) + 1)]  # name without extension
            name = j.core.text.strip_to_ascii_dense(name)

            namespace = j.core.text.strip_to_ascii_dense(namespace)

            if not namespace == "":
                ds = self.docsite_get(namespace)
                res = self._items_get(name, ds=ds)

                # found so will return & remember
                if len(res) == 1:
                    self._pointer_cache[key] = res[0]
                    return res

                # did not find so namespace does not count

            res = self._items_get(name=name, ext=ext)

            if (first and len(res) == 0) or not len(res) == 1:
                if die:
                    raise j.exceptions.Input(
                        message="Cannot find item with name:%s in namespace:'%s'" % (name, namespace)
                    )
                else:
                    self._pointer_cache[key] = None
            else:
                self._pointer_cache[key] = res[0]

        return self._pointer_cache[key]

    def _items_get(self, name, ext, ds=None, res=[]):
        """
        @param ds = DocSite, optional, if specified then will only look there
        """

        if ds is not None:

            if ext in ["md"]:
                find_method = ds.doc_get
            if ext in ["html", "htm"]:
                find_method = ds.html_get
            else:
                find_method = ds.file_get

            res0 = find_method(name=name + "." + ext, die=False)

            if res0 is not None:
                # we have a match, lets add to results
                res.append(res0)

        else:
            for key, ds in self.docsites.items():
                res = self._items_get(name=name, ext=ext, ds=ds, res=res)

        return res

    def def_get(self, name):
        name = j.core.text.strip_to_ascii_dense(name)
        if name not in self.defs:
            raise j.exceptions.Base("cannot find def:%s" % name)
        return self.defs[name]

    def docsite_get(self, name, die=True):
        name = j.core.text.strip_to_ascii_dense(name)
        name = name.lower()
        if name in self.docsites:
            return self.docsites[name]
        if die:
            raise j.exceptions.Input(message="Cannot find docsite with name:%s" % name)
        else:
            return None

    def webserver(self, watch=True, branch="master", sonic_server=None):
        """

        :param watch: to reload the changed data immediately
        :param branch: branch to download
        :param sonic_server: NOT USED YET #TODO:*1
        :return:
        """
        raise j.exceptions.Base("no longer ok, need to use j.servers.openresty")
        url = "https://github.com/threefoldtech/OpenPublish"
        server_path = j.clients.git.getContentPathFromURLorPath(url)
        url = "https://github.com/threefoldtech/jumpscaleX_weblibs"
        weblibs_path = j.clients.git.getContentPathFromURLorPath(url)
        j.sal.fs.symlink(
            "{}/static".format(weblibs_path), "{}/static/weblibs".format(server_path), overwriteTarget=False
        )
        cmd = "cd {0} && moonc . && lapis server".format(server_path)
        j.servers.tmux.execute(cmd, reset=False)

        if watch:
            watcher = Watcher(self.docsites)

            threads = list()
            threads.append(gevent.spawn(self.syncer, branch=branch))
            threads.append(gevent.spawn(watcher.start))

            gevent.joinall(threads)

    def syncer(self, branch):
        print("syncer started, will reload every 5 mins")
        while True:
            print("Reloading")
            self.load_wikis(branch=branch)
            gevent.sleep(300)

    def load_wikis(self, branch="master"):
        url = "https://github.com/threefoldfoundation/info_tokens/tree/%s/docs" % branch
        tf_tokens = self.load(url, name="tokens")
        tf_tokens.write()

        url = "https://github.com/threefoldfoundation/info_foundation/tree/%s/docs" % branch
        tf_foundation = self.load(url, name="foundation")
        tf_foundation.write()

        url = "https://github.com/threefoldfoundation/info_grid/tree/%s/docs" % branch
        tf_grid = self.load(url, name="grid")
        tf_grid.write()

        url = "https://github.com/BetterToken/info_bettertoken/tree/%s/docs" % branch
        tf_grid = self.load(url, name="bettertoken")
        tf_grid.write()

        url = "https://github.com/harvested-io/info_harvested.io/tree/%s/docs" % branch
        tf_grid = self.load(url, name="harvested")
        tf_grid.write()

        url = "https://github.com/freeflownation/info_freeflowevents/tree/%s/docs" % branch
        ff_event_wiki = self.load(url, name="freeflowevent")
        ff_event_wiki.write()

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/99")
    def test2(self):
        url = (
            "https://github.com/threefoldtech/jumpscaleX_core/tree/master/docs/tools/wiki/docsites/examples/docs/"
        )
        examples = j.tools.markdowndocs.load(url, name="examples")
        examples.write()

        j.servers.threebot.get("test").start(background=True)

        import webbrowser

        webbrowser.open("http://localhost:8090/wiki/examples#/test_include")

    @skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/99")
    def test(self, name="", watch=False):
        """
        kosmos 'j.tools.markdowndocs.test()
        """
        self._tests_run(name=name)

        url = "https://github.com/abom/test_custom_md/tree/master/docs"
        ds = self.load(url, name="test")

        doc = ds.doc_get("test")
        for link in doc.links:
            print(link)

        doci = ds.doc_get("test_include")

        print(doci.markdown_obj)

        print("### PROCESSED MARKDOWN DOC")

        # should contain content of https://github.com/abom/test_include_md/blob/master/docs/include_me.md
        assert "![image](img1.svg?sanitize=true)" in doci.markdown

        print("test of docsite done")

        # next will rewrite the full pre-processed docsite
        ds.write()

        url = "https://github.com/threefoldfoundation/info_tokens/tree/master/docs"
        ds4 = self.load(url, name="tf_tokens")
        ds4.write()

        url = "https://github.com/threefoldfoundation/info_foundation/tree/development/docs"
        ds5 = self.load(url, name="tf_foundation")
        ds5.write()

        url = "https://github.com/threefoldfoundation/info_grid/tree/development/docs"
        ds6 = self.load(url, name="tf_grid")
        try:
            ds6.write()
        except:
            pass

        url = "https://github.com/threefoldtech/info_tftech/tree/master/docs"
        ds7 = self.load(url, name="tech")
        ds7.write()

        print("TEST FOR MARKDOWN PREPROCESSING IS DONE")

from .GithubClient import GitHubClient
from Jumpscale import j

JSConfigs = j.baseclasses.object_config_collection


class GitHubFactory(JSConfigs):

    __jslocation__ = "j.clients.github"
    _CHILDCLASS = GitHubClient

    def __init__(self):
        self.__imports__ = "PyGithub"
        self._clients = {}
        super(GitHubFactory, self).__init__()

    def issue_class_get(self):
        # return Issue
        from .Issue import Issue

        return Issue

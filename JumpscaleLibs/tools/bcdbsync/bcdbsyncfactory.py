from Jumpscale import j

from .bcdbsync import BCDBSync


class BCDBSyncFactory(j.baseclasses.object_config_collection_testtools):
    __jslocation__ = "j.tools.bcdbsync"

    _CHILDCLASS = BCDBSync

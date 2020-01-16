from Jumpscale import j
from .GDriveClient import GDriveClient

JSConfigs = j.baseclasses.object_config_collection


class GDriveFactory(JSConfigs):

    __jslocation__ = "j.clients.gdrive"
    _CHILDCLASS = GDriveClient

    def get_from_file(self, name, path):
        """Create a client instance with name <name> and info in credentials file at <path>

        :param name: instance name
        :type name: string
        :param path: path to the credentials file
        :type path: string
        """
        if not name or not path:
            raise j.exceptions.Input("Neither path nor name can be empty")

        creds = j.data.serializers.json.load(path)
        return self.get(name=name, info=j.data.serializers.json.dumps(creds))
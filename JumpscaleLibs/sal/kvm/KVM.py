from Jumpscale import j
from .Network import Network
from .Interface import Interface
from .Disk import Disk
from .Pool import Pool
from .StorageController import StorageController
from .KVMController import KVMController
from .Machine import Machine
from .CloudMachine import CloudMachine
from .MachineSnapshot import MachineSnapshot

JSBASE = j.baseclasses.object


class KVM(j.baseclasses.object):
    # check https://github.com/threefoldtech/jumpscaleX_libs/issues/95

    def _init(self, **kwargs):
        self.__imports__ = "libvirt-python"
        self.KVMController = KVMController
        self.Machine = Machine
        self.MachineSnapshot = MachineSnapshot
        self.Network = Network
        self.Interface = Interface
        self.Disk = Disk
        self.Pool = Pool
        self.StorageController = StorageController
        self.CloudMachine = CloudMachine

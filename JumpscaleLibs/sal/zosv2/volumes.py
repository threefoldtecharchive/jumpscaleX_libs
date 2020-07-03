from .id import _next_workload_id
from Jumpscale import j


class VolumesGenerator:
    def __init__(self):
        self._model = j.data.schema.get_from_url("tfgrid.workloads.reservation.volume.1")

    def create(self, node_id, size=5, type="HDD"):
        """
        add a volume to the reservation
        
        :param reservation: reservation where to add the volume
        :type reservation: tfgrid.workloads.reservation.1)
        :param node_id: id of the node where to reserve the volume
        :type node_id: str
        :param size: size in GiB, defaults to 5
        :type size: int, optional
        :param type: type of disk to use. Can be SSD or HDD
        :type type: str, optional
        :return: the newly created volume object
        :rtype: tfgrid.workloads.reservation.volume.1
        """

        if type not in ["SSD", "HDD"]:
            raise j.excpetions.Input("volume type can only be SSD or HDD")

        volume = self._model.new()
        volume.size = size
        volume.type = type
        volume.info.node_id = node_id
        volume.info.workload_type = "VOLUME"
        return volume

    def attach(self, container, volume, mount_point):
        """
        attach a volume to a container

        the volume must be defined in the same reservation

        container : container object from create_container function
        volume: Volume object that get from add_volume function
        mount_point : path where to mount the volume in the container
        """
        vol = container.volumes.new()
        vol.volume_id = f"-{volume.workload_id}"
        vol.mountpoint = mount_point

    def attach_existing(self, container, volume_id, mount_point):
        """
        attach an existing volume to a container

        the volume must already exist on the node

        container : container object from create_container function
        volume_id: the complete volume ID, format should be '{reservation.id}-{volume.workload_id}'
        mount_point : path where to mount the volume in the container
        """
        vol = container.volumes.new()
        vol.volume_id = volume_id
        vol.mountpoint = mount_point

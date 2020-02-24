class VolumesGenerator:
    def create(self, reservation, node_id, volume_size=5, volume_type="SSD"):
        """
        add a volume to the reservation
        
        :param reservation: reservation where to add the volume
        :type reservation: tfgrid.workloads.reservation.1)
        :param node_id: id of the node where to reserve the volume
        :type node_id: str
        :param volume_size: size in GiB, defaults to 5
        :type volume_size: int, optional
        :param volume_type: type of disk to use. Can be SSD or HDD
        :type volume_type: str, optional
        :return: the newly created volume object
        :rtype: tfgrid.workloads.reservation.volume.1
        """

        if volume_type not in ["SSD", "HHD"]:
            raise j.excpetions.Input("volume type can only be SSD or HDD")

        volume = reservation.data_reservation.volumes.new()
        volume.workload_id = _next_workload_id(reservation)
        volume.size = volume_size
        volume.type = volume_type
        volume.node_id = node_id
        return volume

    def attach(self, container, volume, mount_point):
        """
        container : container object from create_container function
        volume: Volume object that get from add_volume function
        mount_point : path where to mount the volume in the container
        """
        vol = container.volumes.new()
        # here we reference the volume created in the same reservation
        vol.workload_id = _next_workload_id(reservation)
        # TODO: need to check if it's a volume in this reservation or an already existing one
        vol.volume_id = f"-{volume.workload_id}"
        vol.mountpoint = mount_point

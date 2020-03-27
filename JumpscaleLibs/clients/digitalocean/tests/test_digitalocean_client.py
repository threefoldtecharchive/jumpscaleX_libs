import os, time, uuid, subprocess
from Jumpscale import j
from random import randint


def info(message):
    j.tools.logger._log_info(message)


def os_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = process.communicate()
    return output, error


project_name = ""
token = ""
ssh_key = ""

RAND = randint(1, 1000)
NAME = "DigitalOcean_{}".format(RAND)
DO_CLIENT = j.clients.digitalocean.get(name=NAME, token_=token)

skip = j.baseclasses.testtools._skip


@skip("https://github.com/threefoldtech/zeroCI/issues/30, This test can be run manually")
def before_all():
    try:
        global token, ssh_key
        token = os.environ["DO_TOKEN"]
        ssh_key = os.environ["DO_SSHKEY"]
    except KeyError:
        raise Exception("You need to set Digital ocean token and ssh_key name as an environmental variables")
    info("setUp!")
    info("create DigitalOcean client")
    info("create a DigitalOcean project")
    global project_name
    project_name = "DELETEME_DO_TEST_{}".format(RAND)
    DO_CLIENT.project_create(project_name, "testing", description="testing project", is_default=False)
    if "TEST_DO" not in [project.name for project in DO_CLIENT.projects]:
        DO_CLIENT.project_create("TEST_DO", "testing", description="testing project", is_default=True)


def after_all():
    info("tearDown!")
    info("grep all projects which start with name DELETEME_DO_TEST name")
    pro_list = []
    for project in DO_CLIENT.projects:
        pro_list.append(project.name)
    DELETEME_DO_TEST_PRO = [project for project in pro_list if "DELETEME_DO_TEST" in project]
    info("delete all droplets in DELETEME_DO_TEST project")
    for project in DELETEME_DO_TEST_PRO:
        time.sleep(30)
        info("delete all droplets in {} project".format(project))
        DO_CLIENT.droplets_all_delete(project=project, interactive=False)
        info("delete project {}".format(project))
        DO_CLIENT.project_delete(project)
    info("deleting DigitalOcean client")
    DO_CLIENT.delete()


def droplet_create(name, delete_option, project_name):
    """
    method to create a droplet.

    #. create a droplet in ams3 region, using ubuntu 18.04 image, 1vcpu-2gb slug size, and with name test-DO-client
        with (delete=False) option.

    :param project_name: project where the new created droplet will be create.
    :type project_name: str
    :param delete_option: delete option
    :type delete_option: bool.
    :param name: the name of droplet I need to create.
    :type name: str.
    :return: process_id, ip, port.
    """
    info("create first droplet with option delete=False")
    test_create_first = DO_CLIENT.droplet_create(
        name=name,
        region="Amsterdam 3",
        image="ubuntu 18.04",
        size_slug="s-1vcpu-2gb",
        sshkey=ssh_key,
        delete=delete_option,
        project_name=project_name,
    )
    if test_create_first:
        info("grep first process_id, ip and port")
        process_id = test_create_first[0].id
        ip = test_create_first[1].addr
        port = test_create_first[1].port
    else:
        return False
    return process_id, ip, port


def check_droplet_create(ip, port):
    """
    method to check that the droplet is created correctly.
    #. check that the droplet is up and running, ssh and execute certain ping google.com once,
       and try to create file in /tmp/ and make sure that the file is created.

    :param ip: droplet ip
    :type ip: str
    :param port: port number
    :type port: int
    :return: True if droplet is created correctly.
    """

    time.sleep(30)
    info("droplet ip {}, port {}".format(ip, port))
    info("check that droplet is created correctly, ssh to the machine, and ping google and check the output")
    output, error = os_command(
        'ssh -o "StrictHostKeyChecking no" root@{} -p {} \
                                                 "ping -c 1 google.com"'.format(
            ip, port
        )
    )
    if "0% packet loss" in output.decode():
        info("try to create a file and check the existence of this file")
        output, error = os_command('ssh root@{} -p {} "touch /tmp/test"'.format(ip, port))
        if not error:
            output, error = os_command('ssh root@{} -p {} "ls /tmp/test"'.format(ip, port))
            if "/tmp/test\n" == output.decode():
                return True
            else:
                return False
        else:
            return False
    else:
        return False


def project_create(project_name, is_default):
    """
    method to create a project, and return True if project is created correctly and False if not created correctly.

    :param project_name: project_name which we need to create a project with it
    :param is_default: is_default option.
    :type is_default: bool.
    :return: bool.
    """
    info("create a project with {} name".format(project_name))
    DO_CLIENT.project_create(project_name, "testing", description="testing project", is_default=is_default)
    info("use projects method to check the project existsnce in project list")
    projects = []
    for project in DO_CLIENT.projects:
        projects.append(project.name)
    if project_name in projects:
        return True
    else:
        return False


def test001_droplet_create_with_new_name():
    """
    TC 440
    Test case to check droplet create method with certain name, and delete option =True, should success.

    **Test scenario**
    #. create a droplet with certain name, with delete option=True, should success.
    """

    droplet_name = "Droplet-{}".format(RAND)
    info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
    process_id, ip, port = droplet_create(droplet_name, True, project_name)
    info("check the process_id to make sure that the droplet is created correctly")
    assert process_id
    assert check_droplet_create(ip, port)


def test002_droplet_create_with_an_exists_name_delete_False_option():
    """
    TC 441
    Test case to check droplet create with an exists name, with option delete=False,
    should return the same process_id, ip, and port.

    **Test scenario**
    #. create a new droplet, with certain name, redo it again with the same name, with option delete=False.
    #. the process_id, ip, and port should be the same in the two times.
    """

    droplet_name = "Droplet-{}".format(RAND)
    info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
    process_id_first, ip_first, port_first = droplet_create(droplet_name, False, project_name)
    info("check the process_id to make sure that the droplet is created correctly")
    assert process_id_first
    assert check_droplet_create(ip_first, port_first)
    info("create droplet again with the same name, and option delete=False")
    process_id_second, ip_second, port_second = droplet_create(droplet_name, False, project_name)
    info("check the process_id to make sure that the droplet is created correctly")
    assert process_id_second
    info("check that the process_id, ip, and port in the second droplet is the same in the first one")
    assert process_id_first == process_id_second, "The process_id should be the same"
    assert ip_first == ip_second, "The ip should be the same"
    assert port_first == port_second, "The port should be the same"


def test003_droplet_create_with_an_exists_name_delete_True_option():
    """
    TC 442
    Test case to check droplet create with an exists name, with option delete=True,
    should return different process_id, ip, and port.

    **Test scenario**
    #. create a new droplet, with certain name, redo it again with the same name, with option delete=True.
    #. the process_id, ip, and port shouldn't be the same.
    """

    droplet_name = "Droplet-{}".format(RAND)
    info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
    process_id_first, ip_first, port_first = droplet_create(droplet_name, True, project_name)
    info("check the process_id to make sure that the droplet is created correctly")
    assert process_id_first
    assert check_droplet_create(ip_first, port_first)
    info("create droplet again with the same name, and option delete=True")
    process_id_second, ip_second, port_second = droplet_create(droplet_name, True, project_name)
    info("check the process_id to make sure that the droplet is created correctly")
    assert process_id_second
    assert check_droplet_create(ip_second, port_second)
    info("check that the process_id, ip, and port in the second droplet aren't the same in the first one")
    assert process_id_first != process_id_second, "The process_id shouldn't be the same"
    assert ip_first != ip_second, "The ip shouldn't be the same"


def test004_droplet_exists_with_an_exists_name():
    """
    TC 443
    Test case for droplet_exists method check in DO client, with exists name.

    **Test scenario**
    #. create a droplet with certain name,using check_droplet_method.
    #. check the existence of this droplet using droplet_exists method, should pass.
    """

    droplet_name = "Droplet-{}".format(RAND)
    info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
    process_id, ip, port = droplet_create(droplet_name, True, project_name)
    info("check the process_id to make sure that the droplet is created correctly")
    assert process_id
    assert check_droplet_create(ip, port)
    info("check the exists of {}  droplet using droplet_exists method".format(droplet_name))
    assert DO_CLIENT.droplet_exists(droplet_name)


def test005_droplet_get_with_an_exists_name():
    """
    TC 444
    Test case to test droplet_get method in DO client, with an exists name.

    **Test scenario**
    #. create a droplet with certain name,using check_droplet_method.
    #. use droplet_get method to check it's id.
    """

    droplet_name = "Droplet-{}".format(RAND)
    info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
    process_id, ip, port = droplet_create(droplet_name, True, project_name)
    info("check the process_id to make sure that the droplet is created correctly")
    assert process_id
    assert check_droplet_create(ip, port)
    info("test droplet_get method")
    assert DO_CLIENT.droplet_get(droplet_name).id


def test006_droplet_all_shutdown():
    """
    TC 447
    Test case for droplet_all_shutdown method

    **Test scenario**
    #. create 2 droplets in DELETEME_DO_TEST project.
    #. use this method to shutdown all droplets in this project.
    #. try to ping droplets, ips
    """
    ips = []
    for i in range(2):
        droplet_name = "Droplet-{}-{}".format(RAND, i)
        info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        process_id, ip, port = droplet_create(droplet_name, True, project_name)
        info("check the process_id to make sure that the droplet is created correctly")
        assert process_id
        assert check_droplet_create(ip, port)
        ips.append(ip)
    info("use droplets_all_shutdown to shutdown all droplets in {} project".format(project_name))
    DO_CLIENT.droplets_all_shutdown(project=project_name)
    info("check that droplets are shutdown correctly")
    print(ips)
    time.sleep(30)
    for ip in ips:
        output, error = os_command("ping -c 5 {}".format(ip))
        assert "100% packet loss" in output.decode()


def test007_droplet_all_delete():
    """
    TC 448
    Test case for droplet_all_delete method

    #. create 2 droplets in DELETEME_DO_TEST project.
    #. use this method to delete all droplets in this project.
    #. trying to ping droplets' ip, should fail.
    """

    ips = []
    droplet_name_list = []
    for i in range(2):
        droplet_name = "Droplet-{}-{}".format(RAND, i)
        info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        process_id, ip, port = droplet_create(droplet_name, True, project_name)
        info("check the process_id to make sure that the droplet is created correctly")
        assert process_id
        assert check_droplet_create(ip, port)
        ips.append(ip)
        droplet_name_list.append(droplet_name)
    info("check that droplets are delete correctly")
    DO_CLIENT.droplets_all_delete(project=project_name, interactive=False)
    info(
        "use droplet_get method to check that droplet_all_delete method delete all droplets in {} project".format(
            project_name
        )
    )
    time.sleep(30)
    for ip in ips:
        output, error = os_command("ping -c 5 {}".format(ip))
        assert "100% packet loss" in output.decode()


def test008_image_get_with_exist_name():
    """
    TC 649
    test case to check image_get method with 'ubuntu 18.04' name, should success.

    **Test scenario**
    #. get the image name with (ubuntu 18.04).
    #. check that the command is executed without any error, and the output equal to '18.04.3 (LTS) x64'.
    """
    info("get the image name with 'ubuntu 18.04' name")
    image_get = DO_CLIENT.image_get("ubuntu 18.04")
    info("check that the command is executed without any error")
    assert image_get
    info("the output equal to '18.04.3 (LTS) x64'.")
    assert "18.04.3 (LTS) x64" == image_get.name


def test009_image_names_get():
    """
    TC 451
    test case to check image_names_get method

    **Test scenario**
    #. use image_names_get method to get all image name.
    #. check the output of this command.
    """
    info("use image_names_get method to get all image names")
    image_list = DO_CLIENT.image_names_get()
    assert "CoreOS 2247.5.0 (stable)" in image_list


def test010_droplets_list_without_project_name():
    """
    TC 452
    Test case to check droplet_list method, without project_name option

    **Test scenario**
    #. Check the output of droplets_list without project option, should equal droplets output.
    """
    info("check that droplets_list doesn't raise an error")
    assert DO_CLIENT.droplets_list()
    info("check that output of droplets_list equals droplets output")
    assert DO_CLIENT.droplets_list() == DO_CLIENT.droplets
    info("check the output of droplets_list with a non exists project name")


def test011_droplets_list_with_valid_project_name():
    """
    TC 454
    Test case to test droplets_list method with an exists project_name, should success.

    **Test scenario**
    #. create 2 droplets.
    #. use droplets_list to list the droplets in DELETEME_DO_TEST project.
    """

    info("create 2 droplets in {} project".format(project_name))
    droplet_name_list = []
    for i in range(2):
        droplet_name = "Droplet-{}-{}".format(RAND, i)
        info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        process_id, ip, port = droplet_create(droplet_name, True, project_name)
        info("check the process_id to make sure that the droplet is created correctly")
        assert process_id
        assert check_droplet_create(ip, port)
        droplet_name_list.append(droplet_name)
    info("check that droplets_list exists correctly without errors")
    assert DO_CLIENT.droplets_list(project=project_name)
    info("check that the output of droplets_list doesn't equal to the output of droplets")
    assert DO_CLIENT.droplets_list(project=project_name) != DO_CLIENT.droplets
    info("check the new 2 created droplets are in the output of droplets_list")
    droplets_name = []
    for droplet in DO_CLIENT.droplets_list(project=project_name):
        droplets_name.append(droplet.name)
    assert sorted(droplets_name) == sorted(droplet_name_list)


def test012_create_project_with_new_name_is_default_False():
    """
    TC 455
    Test case to check create_project method, with is_default=False option

    **Test scenario**
    #. use project_create method to create a new project, with option is_default=False.
    #. make sure that the new created droplet, not in a project.
    """

    project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
    info("create a project with {} and make sure that it's created correctly".format(project_name))
    assert project_create(project_name, False)
    droplet_name = "Droplet-{}".format(RAND)
    info("create a new droplet {} ".format(droplet_name))
    info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
    test_create_first = DO_CLIENT.droplet_create(
        name=droplet_name,
        region="Amsterdam 3",
        image="ubuntu 18.04",
        size_slug="s-1vcpu-2gb",
        sshkey=ssh_key,
        delete=True,
    )
    info("check the process_id to make sure that the droplet is created correctly")
    assert test_create_first[0].id
    ip = test_create_first[1].addr
    port = test_create_first[1].port
    assert check_droplet_create(ip, port)
    info("make sure that the new created droplet {}, not in {} project".format(droplet_name, project_name))
    assert len(DO_CLIENT.droplets_list(project=project_name)) == 0


def test013_create_project_new_name_is_default_True():
    """
    TC 456
    Test case for project create method in DO client, with option is_default=True

    **Test scenario**
    #. use project_create method to create a new project, with option is_default=True.
    #. make sure that the new created droplet, in a project.
    """
    project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
    info("create a project with {} and make sure that it's created correctly".format(project_name))
    assert project_create(project_name, True)
    droplet_name = "Droplet-{}".format(RAND)
    info("create a new droplet {} ".format(droplet_name))
    info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
    test_create_first = DO_CLIENT.droplet_create(
        name=droplet_name, region="Amsterdam 3", image="ubuntu 18.04", size_slug="s-1vcpu-2gb", sshkey=ssh_key
    )
    info("check the process_id to make sure that the droplet is created correctly")
    assert test_create_first[0].id
    ip = test_create_first[1].addr
    port = test_create_first[1].port
    assert check_droplet_create(ip, port)
    info("make sure that the new created droplet {}, is in {} project".format(droplet_name, project_name))
    assert len(DO_CLIENT.droplets_list(project=project_name)) == 1
    DO_CLIENT.project_get("TEST_DO").update(is_default=True)


def test014_projects():
    """
    TC 458
    Test case for projects method in DO client.

    **Test scenario**
    #. create a projects using project_create method.
    #. check the exists of this project in project list, using projects method.
    """
    info("create a project")
    project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
    assert project_create(project_name, False)
    info("check that projects method run without errors")
    assert DO_CLIENT.projects
    info("check the just created project is in project list")
    projects = DO_CLIENT.projects
    projects_name = []
    for project in projects:
        projects_name.append(project.name)
    assert project_name in projects_name


def test015_droplets():
    """
    TC 459
    Test case to check the output of droplets method in DO client.

    **Test scenario**
    #. check that droplets doesn't raise an error.
    #. check that the output of droplets equals to droplets_list without a project option
    """
    info("check that droplets method doesn't raise an error")
    assert DO_CLIENT.droplets
    info("check that the output of droplets_list method equals droplets method output")
    assert DO_CLIENT.droplets == DO_CLIENT.droplets_list()


def test016_get_project_with_correct_name():
    """
    TC 460
    Test case for check the get project with correct name, should pass.

    **Test scenario**
    #. create a project, make sure that project is created correctly.
    #. try to get the project name, should success.
    """
    info("create a project with certain name")
    project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
    assert project_create(project_name, False)
    info("use project_get method to check the exists of {} project".format(project_name))
    assert DO_CLIENT.project_get(project_name)
    assert project_name == DO_CLIENT.project_get(project_name).name


def test017_get_project_with_wrong_name():
    """
    TC 461
    Test case for check the get project with wrong name.

    **Test scenario**
    #. create a project, make sure that project is created correctly.
    #. try to get it
    #. delete the project, and redo it again.
    #. try to get the project name, should fail.
    """
    project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
    info("create a project with {} name".format(project_name))
    assert project_create(project_name, False)
    DO_CLIENT.project_delete(project_name)
    info("check that {} project, doesn't exist in projects list".format(project_name))
    projects = []
    for project in DO_CLIENT.projects:
        projects.append(project.name)
    assert project_name != projects


def test018_delete_project_with_exist_name():
    """
    TC 462
    Test case for delete project method in DO client

    **Test scenario**
    #. create a project with certain name.
    #. use project_delete method to delete this project.
    """
    project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
    info("create {} project".format(project_name))
    assert project_create(project_name, False)
    info("delete {} project".format(project_name))
    DO_CLIENT.project_delete(project_name)
    info("make sure that the {} project isn't in project list".format(project_name))
    projects = []
    for project in DO_CLIENT.projects:
        projects.append(project.name)
    assert project_name != projects


def test019_sshkey_get_with_exist_name():
    """
    TC 664
    test case to check sshkey_get method with certain name, should success.

    **Test scenario**
    #. get the sshkey with correct sshkey
    #. check that the command is executed without any error, and the output equal to the sshkey which we use.
    """
    info("get sshkey with correct name {}".format(ssh_key))
    sshkey_get = DO_CLIENT.sshkey_get(name=ssh_key)
    info("check that the command is executed without any error")
    assert sshkey_get
    info("the output equal to the sshkey which we use.")
    assert ssh_key == sshkey_get.name


def test020_region_get_with_exist_name():
    """
    TC 666
    test case to check region_get method with ams3 name

    **Test scenario**
    #. check the existence of region called ams3.
    #. check that the command is executed without any error, and the region name equal to 'Amsterdam 3'.
    """
    info("get the region with name ams3")
    region = DO_CLIENT.region_get("ams3")
    info("check that the command is executed without any error")
    assert region
    info("the region name equal to 'Amsterdam 3'")
    assert "Amsterdam 3" == region.name

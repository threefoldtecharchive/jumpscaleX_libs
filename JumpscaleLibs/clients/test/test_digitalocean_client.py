import time
from Jumpscale import j
from random import randint
from testconfig import config
from base_test import BaseTest


class DigitalOceanClient(BaseTest):
    LOGGER = BaseTest.LOGGER
    LOGGER.add("digital_ocean_{time}.log")
    token = config["digital_ocean"]["token"]
    ssh_key = config["digital_ocean"]["sshkey"]
    RAND = randint(1, 1000)
    NAME = "DigitalOcean_{}".format(RAND)
    DO_CLIENT = j.clients.digitalocean.get(name=NAME, token_=token)

    @classmethod
    def setUpClass(cls):
        cls.info("setUp!")
        cls.info("create DigitalOcean client")
        cls.info("create a DigitalOcean project")
        cls.project_name = "DELETEME_DO_TEST_{}".format(cls.RAND)
        cls.DO_CLIENT.project_create(cls.project_name, "testing", description="testing project", is_default=False)
        if "TEST_DO" not in [project.name for project in cls.DO_CLIENT.projects]:
            cls.DO_CLIENT.project_create("TEST_DO", "testing", description="testing project", is_default=True)

    @classmethod
    def tearDownClass(cls):
        cls.info("tearDown!")
        cls.info("grep all projects which start with name DELETEME_DO_TEST name")
        pro_list = []
        for project in cls.DO_CLIENT.projects:
            pro_list.append(project.name)
        DELETEME_DO_TEST_PRO = [project for project in pro_list if 'DELETEME_DO_TEST' in project]
        cls.info("delete all droplets in DELETEME_DO_TEST project")
        for project in DELETEME_DO_TEST_PRO:
            cls.info("delete all droplets in {} project".format(project))
            cls.DO_CLIENT.doplets_all_delete(project=project, interactive=False)
            cls.info("delete project {}".format(project))
            cls.DO_CLIENT.project_delete(project)
        cls.info("deleting DigitalOcean client")
        cls.DO_CLIENT.delete()

    def setUp(self):
        print("\t")
        self.info("* Test case : {}".format(self._testMethodName))

    def droplet_create(self, name, delete_option, project_name):
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
        self.info("create first droplet with option delete=False")
        test_create_first = self.DO_CLIENT.droplet_create(
            name=name,
            region="Amsterdam 3",
            image="ubuntu 18.04",
            size_slug="s-1vcpu-2gb",
            sshkey=self.ssh_key,
            delete=delete_option,
            project_name=project_name
        )
        if test_create_first:
            self.info("grep first process_id, ip and port")
            process_id = test_create_first[0].id
            ip = test_create_first[1].addr
            port = test_create_first[1].port
        else:
            return False
        return process_id, ip, port

    def check_droplet_create(self, ip, port):
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
        self.info("droplet ip {}, port {}".format(ip, port))
        self.info("check that droplet is created correctly, ssh to the machine, and ping google and check the output")
        output, error = self.os_command(
            'ssh -o "StrictHostKeyChecking no" root@{} -p {} \
                                                     "ping -c 1 google.com"'.format(ip, port)
        )
        if "0% packet loss" in output.decode():
            self.info("try to create a file and check the existence of this file")
            output, error = self.os_command('ssh root@{} -p {} "touch /tmp/test"'.format(ip, port))
            if not error:
                output, error = self.os_command('ssh root@{} -p {} "ls /tmp/test"'.format(ip, port))
                if "/tmp/test\n" == output.decode():
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def project_create(self, project_name, is_default):
        """
        method to create a project, and return True if project is created correctly and False if not created correctly.

        :param project_name: project_name which we need to create a project with it
        :param is_default: is_default option.
        :type is_default: bool.
        :return: bool.
        """
        self.info("create a project with {} name".format(project_name))
        self.DO_CLIENT.project_create(project_name, "testing", description='testing project', is_default=is_default)
        self.info("use projects method to check the project existsnce in project list")
        projects = []
        for project in self.DO_CLIENT.projects:
            projects.append(project.name)
        if project_name in projects:
            return True
        else:
            return False

    def test001_droplet_create_with_new_name(self):
        """
        TC 440
        Test case to check droplet create method with certain name, and delete option =True, should success.

        **Test scenario**
        #. create a droplet with certain name, with delete option=True, should success.
        """

        droplet_name = "Droplet-{}".format(self.RAND)
        self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        process_id, ip, port = self.droplet_create(droplet_name, True, self.project_name)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(process_id)
        self.assertTrue(self.check_droplet_create(ip, port))

    def test002_droplet_create_with_an_exists_name_delete_False_option(self):
        """
        TC 441
        Test case to check droplet create with an exists name, with option delete=False,
        should return the same process_id, ip, and port.

        **Test scenario**
        #. create a new droplet, with certain name, redo it again with the same name, with option delete=False.
        #. the process_id, ip, and port should be the same in the two times.
        """

        droplet_name = "Droplet-{}".format(self.RAND)
        self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        process_id_first, ip_first, port_first = self.droplet_create(droplet_name, False, self.project_name)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(process_id_first)
        self.assertTrue(self.check_droplet_create(ip_first, port_first))
        self.info("create droplet again with the same name, and option delete=False")
        process_id_second, ip_second, port_second = self.droplet_create(droplet_name, False, self.project_name)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(process_id_second)
        self.info("check that the process_id, ip, and port in the second droplet is the same in the first one")
        self.assertEqual(process_id_first, process_id_second, "The process_id should be the same")
        self.assertEqual(ip_first, ip_second, "The ip should be the same")
        self.assertEqual(port_first, port_second, "The port should be the same")

    def test003_droplet_create_with_an_exists_name_delete_True_option(self):
        """
        TC 442
        Test case to check droplet create with an exists name, with option delete=True,
        should return different process_id, ip, and port.

        **Test scenario**
        #. create a new droplet, with certain name, redo it again with the same name, with option delete=True.
        #. the process_id, ip, and port shouldn't be the same.
        """

        droplet_name = "Droplet-{}".format(self.RAND)
        self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        process_id_first, ip_first, port_first = self.droplet_create(droplet_name, True, self.project_name)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(process_id_first)
        self.assertTrue(self.check_droplet_create(ip_first, port_first))
        self.info("create droplet again with the same name, and option delete=True")
        process_id_second, ip_second, port_second = self.droplet_create(droplet_name, True, self.project_name)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(process_id_second)
        self.assertTrue(self.check_droplet_create(ip_second, port_second))
        self.info("check that the process_id, ip, and port in the second droplet aren't the same in the first one")
        self.assertNotEqual(process_id_first, process_id_second, "The process_id shouldn't be the same")
        self.assertNotEqual(ip_first, ip_second, "The ip shouldn't be the same")

    def test004_droplet_exists_with_an_exists_name(self):
        """
        TC 443
        Test case for droplet_exists method check in DO client, with exists name.

        **Test scenario**
        #. create a droplet with certain name,using check_droplet_method.
        #. check the existence of this droplet using droplet_exists method, should pass.
        """

        droplet_name = "Droplet-{}".format(self.RAND)
        self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        process_id, ip, port = self.droplet_create(droplet_name, True, self.project_name)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(process_id)
        self.assertTrue(self.check_droplet_create(ip, port))
        self.info("check the exists of {}  droplet using droplet_exists method".format(droplet_name))
        self.assertTrue(self.DO_CLIENT.droplet_exists(droplet_name))

    def test005_droplet_exists_with_non_exists_name(self):
        """
        TC 468
        Test case to test droplet_exists method in DO client, with non_exists name.

        **Test scenario**
        #. try to exist a droplet with random name.
        """
        droplet_name = "BLABLABLA_{}".format(randint(1, 1000))
        self.info("try to check if there is droplet with name {} using droplet_exists method, it shouldn't be exists"
                  .format(droplet_name)
                  )
        self.assertFalse(self.DO_CLIENT.droplet_exists(droplet_name))

    def test006_droplet_get_with_an_exists_name(self):
        """
        TC 444
        Test case to test droplet_get method in DO client, with an exists name.

        **Test scenario**
        #. create a droplet with certain name,using check_droplet_method.
        #. use droplet_get method to check it's id.
        """

        droplet_name = "Droplet-{}".format(self.RAND)
        self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        process_id, ip, port = self.droplet_create(droplet_name, True, self.project_name)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(process_id)
        self.assertTrue(self.check_droplet_create(ip, port))
        self.info("test droplet_get method")
        self.assertTrue(self.DO_CLIENT.droplet_get(droplet_name).id)

    def test007_droplet_get_with_non_exists_name(self):
        """
        TC 445
        Test case to test droplet_get method in DO client, with a non exists name.

        **Test scenario**
        #. try to get a droplet with random name.
        """
        droplet_name = "BLABLABLA_{}".format(randint(1, 1000))
        self.info("try to check if there is droplet with name {} using droplet_get method, it shouldn't be exists"
                  .format(droplet_name)
                  )
        with self.assertRaises(Exception):
            self.DO_CLIENT.droplet_get(droplet_name)

    def test008_droplet_all_shutdown(self):
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
            droplet_name = "Droplet-{}-{}".format(self.RAND, i)
            self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
            process_id, ip, port = self.droplet_create(droplet_name, True, self.project_name)
            self.info("check the process_id to make sure that the droplet is created correctly")
            self.assertTrue(process_id)
            self.assertTrue(self.check_droplet_create(ip, port))
            ips.append(ip)
        self.info("use droplets_all_shutdown to shutdown all droplets in {} project".format(self.project_name))
        self.DO_CLIENT.droplets_all_shutdown(project=self.project_name)
        self.info("check that droplets are shutdown correctly")
        print(ips)
        time.sleep(30)
        for ip in ips:
            output, error = self.os_command("ping -c 5 {}".format(ip))
            self.assertIn("100% packet loss", output.decode())

    def test009_droplet_all_delete(self):
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
            droplet_name = "Droplet-{}-{}".format(self.RAND, i)
            self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
            process_id, ip, port = self.droplet_create(droplet_name, True, self.project_name)
            self.info("check the process_id to make sure that the droplet is created correctly")
            self.assertTrue(process_id)
            self.assertTrue(self.check_droplet_create(ip, port))
            ips.append(ip)
            droplet_name_list.append(droplet_name)
        self.info("check that droplets are delete correctly")
        self.DO_CLIENT.droplets_all_delete(project=self.project_name, interactive=False)
        self.info("use droplet_get method to check that droplet_all_delete method delete all droplets in {} project"
                  .format(self.project_name))
        time.sleep(30)
        for ip in ips:
            output, error = self.os_command("ping -c 5 {}".format(ip))
            self.assertIn("100% packet loss", output.decode())

    def test010_image_get_with_exist_name(self):
        """
        TC 649
        test case to check image_get method with 'ubuntu 18.04' name, should success.

        **Test scenario**
        #. get the image name with (ubuntu 18.04).
        #. check that the command is executed without any error, and the output equal to '18.04.3 (LTS) x64'.
        """
        self.info("get the image name with 'ubuntu 18.04' name")
        image_get = self.DO_CLIENT.image_get('ubuntu 18.04')
        self.info("check that the command is executed without any error")
        self.assertTrue(image_get)
        self.info("the output equal to '18.04.3 (LTS) x64'.")
        self.assertEqual('18.04.3 (LTS) x64', image_get.name)

    def test011_image_get_with_non_exist_name(self):
        """
        TC 650
        test case to check image_get method with wrong name, should fail.

        **Test scenario**
        #. get the image name with wrong name.
        #. check that the command raises an error.
        """
        self.info("get the image with 'blabla' name , it should raise an error")
        with self.assertRaises(Exception):
            self.DO_CLIENT.image_get("blabla")

    def test012_image_names_get(self):
        """
        TC 451
        test case to check image_names_get method

        **Test scenario**
        #. use image_names_get method to get all image name.
        #. check the output of this command.
        """
        self.info("use image_names_get method to get all image names")
        image_list = self.DO_CLIENT.image_names_get()
        self.assertIn('CoreOS 2247.5.0 (stable)', image_list)

    def test013_droplets_list_without_project_name(self):
        """
        TC 452
        Test case to check droplet_list method, without project_name option

        **Test scenario**
        #. check the output of droplets_list without ptoject option, should equal droplets output.
        """
        self.info("check that droplets_list doesn't raise an error")
        self.assertTrue(self.DO_CLIENT.droplets_list())
        self.info("check that output of droplets_list equals droplets output")
        self.assertEqual(self.DO_CLIENT.droplets_list(), self.DO_CLIENT.droplets)

    def test014_droplets_list_with_non_exists_project_name(self):
        """
        TC 453
        Test case to check droplets_list with a non-exists project name, should fail.

        **Test scenario**
        #. check the output of droplets_list with non exists project name, should fail.
        """

        self.info("check the output of droplets_list with a non exists project name")
        project_name = "DELETEME_DO_TEST_TEST_{}".format(self.RAND)
        with self.assertRaises(Exception):
            self.DO_CLIENT.droplets_list(project=project_name)

    def test015_droplets_list_with_valid_project_name(self):
        """
        TC 454
        Test case to test droplets_list method with an exists project_name, should success.

        **Test scenario**
        #. create 2 droplets.
        #. use droplets_list to list the droplets in DELETEME_DO_TEST project.
        """

        self.info("create 2 droplets in {} project".format(self.project_name))
        droplet_name_list = []
        for i in range(2):
            droplet_name = "Droplet-{}-{}".format(self.RAND, i)
            self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
            process_id, ip, port = self.droplet_create(droplet_name, True, self.project_name)
            self.info("check the process_id to make sure that the droplet is created correctly")
            self.assertTrue(process_id)
            self.assertTrue(self.check_droplet_create(ip, port))
            droplet_name_list.append(droplet_name)
        self.info("check that droplets_list exists correctly without errors")
        self.assertTrue(self.DO_CLIENT.droplets_list(project=self.project_name))
        self.info("check that the output of droplets_list doesn't equal to the output of droplets")
        self.assertNotEqual(self.DO_CLIENT.droplets_list(project=self.project_name), self.DO_CLIENT.droplets)
        self.info("check the new 2 created droplets are in the output of droplets_list")
        droplets_name = []
        for droplet in (self.DO_CLIENT.droplets_list(project=self.project_name)):
            droplets_name.append(droplet.name)
        self.assertListEqual(sorted(droplets_name), sorted(droplet_name_list))

    def test016_create_project_with_new_name_is_default_False(self):
        """
        TC 455
        Test case to check create_project method, with is_default=False option

        **Test scenario**
        #. use project_create method to create a new project, with option is_default=False.
        #. make sure that the new created droplet, not in a project.
        """

        project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
        self.info("create a project with {} and make sure that it's created correctly".format(project_name))
        self.assertTrue(self.project_create(project_name, False))
        droplet_name = "Droplet-{}".format(self.RAND)
        self.info("create a new droplet {} ".format(droplet_name))
        self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        test_create_first = self.DO_CLIENT.droplet_create(name=droplet_name, region="Amsterdam 3", image="ubuntu 18.04",
                                                          size_slug="s-1vcpu-2gb", sshkey=self.ssh_key, delete=True)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(test_create_first[0].id)
        ip = test_create_first[1].addr
        port = test_create_first[1].port
        self.assertTrue(self.check_droplet_create(ip, port))
        self.info("make sure that the new created droplet {}, not in {} project".format(droplet_name, project_name))
        self.assertEqual(len(self.DO_CLIENT.droplets_list(project=project_name)), 0)

    def test017_create_project_new_name_is_default_True(self):
        """
        TC 456
        Test case for project create method in DO client, with option is_default=True

        **Test scenario**
        #. use project_create method to create a new project, with option is_default=True.
        #. make sure that the new created droplet, in a project.
        """
        project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
        self.info("create a project with {} and make sure that it's created correctly".format(project_name))
        self.assertTrue(self.project_create(project_name, True))
        droplet_name = "Droplet-{}".format(self.RAND)
        self.info("create a new droplet {} ".format(droplet_name))
        self.info("create a new droplet with name {},and check if it created correctly or not".format(droplet_name))
        test_create_first = self.DO_CLIENT.droplet_create(name=droplet_name, region="Amsterdam 3", image="ubuntu 18.04",
                                                          size_slug="s-1vcpu-2gb", sshkey=self.ssh_key)
        self.info("check the process_id to make sure that the droplet is created correctly")
        self.assertTrue(test_create_first[0].id)
        ip = test_create_first[1].addr
        port = test_create_first[1].port
        self.assertTrue(self.check_droplet_create(ip, port))
        self.info("make sure that the new created droplet {}, is in {} project".format(droplet_name, project_name))
        self.assertEqual(len(self.DO_CLIENT.droplets_list(project=project_name)), 1)
        self.DO_CLIENT.project_get("TEST_DO").update(is_default=True)

    def test018_create_project_with_exists_name(self):
        """
        TC 457
        Test case to test project_create method with an exist name, it should raise an error

        **Test scenario**
        #. create a project with an exists name.
        #. redo it again with the same name, it should raise an error.
        """
        project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
        self.info("create a project with {} name".format(project_name))
        self.assertTrue(self.project_create(project_name, False))
        self.info("recreate a project {} again".format(project_name))
        with self.assertRaises(Exception):
            self.DO_CLIENT.project_create(project_name, "testing", description='testing project',  is_default=False)

    def test019_projects(self):
        """
        TC 458
        Test case for projects method in DO client.

        **Test scenario**
        #. create a projects using project_create method.
        #. check the exists of this project in project list, using projects method.
        """
        self.info("create a project")
        project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
        self.assertTrue(self.project_create(project_name, False))
        self.info("check that projects method run without errors")
        self.assertTrue(self.DO_CLIENT.projects)
        self.info("check the just created project is in project list")
        projects = self.DO_CLIENT.projects
        projects_name = []
        for project in projects:
            projects_name.append(project.name)
        self.assertIn(project_name, projects_name)

    def test020_droplets(self):
        """
        TC 459
        Test case to check the output of droplets method in DO client.

        **Test scenario**
        #. check that droplets doesn't raise an error.
        #. check that the output of droplets equals to droplets_list without a project option
        """
        self.info("check that droplets method doesn't raise an error")
        self.assertTrue(self.DO_CLIENT.droplets)
        self.info("check that the output of droplets_list method equals droplets method output")
        self.assertEqual(self.DO_CLIENT.droplets, self.DO_CLIENT.droplets_list())

    def test021_get_project_with_correct_name(self):
        """
        TC 460
        Test case for check the get project with correct name, should pass.

        **Test scenario**
        #. create a project, make sure that project is created correctly.
        #. try to get the project name, should success.
        """
        self.info("create a project with certain name")
        project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
        self.assertTrue(self.project_create(project_name, False))
        self.info("use project_get method to check the exists of {} project".format(project_name))
        self.assertTrue(self.DO_CLIENT.project_get(project_name))
        self.assertEqual(project_name, self.DO_CLIENT.project_get(project_name).name)

    def test022_get_project_with_wrong_name(self):
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
        self.info("create a project with {} name".format(project_name))
        self.assertTrue(self.project_create(project_name, False))
        self.DO_CLIENT.project_delete(project_name)
        self.info("check that {} project, doesn't exist in projects list".format(project_name))
        projects = []
        for project in self.DO_CLIENT.projects:
            projects.append(project.name)
        self.assertNotIn(project_name, projects)

    def test023_delete_project_with_exist_name(self):
        """
        TC 462
        Test case for delete project method in DO client

        **Test scenario**
        #. create a project with certain name.
        #. use project_delete method to delete this project.
        """
        project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
        self.info("create {} project".format(project_name))
        self.assertTrue(self.project_create(project_name, False))
        self.info("delete {} project".format(project_name))
        self.DO_CLIENT.project_delete(project_name)
        self.info("make sure that the {} project isn't in project list".format(project_name))
        projects = []
        for project in self.DO_CLIENT.projects:
            projects.append(project.name)
        self.assertNotIn(project_name, projects)

    def test024_delete_project_with_non_exist_name(self):
        """
        TC 463
        Test case for delete project method in DO client

        **Test scenario**
        #. create a project with certain name.
        #. use project_delete method to delete this project.
        #. redo the last step again. should raise an error.
        """
        project_name = "DELETEME_DO_TEST_{}".format(randint(1, 1000))
        self.info("create {} project".format(project_name))
        self.assertTrue(self.project_create(project_name, False))
        self.info("delete {} project".format(project_name))
        self.DO_CLIENT.project_delete(project_name)
        self.info("try to delete {} project again, should fail".format(project_name))
        with self.assertRaises(Exception):
            self.DO_CLIENT.project_delete(project_name)

    def test025_sshkey_get_with_exist_name(self):
        """
        TC 664
        test case to check sshkey_get method with certain name, should success.

        **Test scenario**
        #. get the sshkey with correct sshkey
        #. check that the command is executed without any error, and the output equal to the sshkey which we use.
        """
        self.info("get sshkey with correct name {}".format(self.ssh_key))
        sshkey_get = self.DO_CLIENT.sshkey_get(name=self.ssh_key)
        self.info("check that the command is executed without any error")
        self.assertTrue(sshkey_get)
        self.info("the output equal to the sshkey which we use.")
        self.assertEqual(self.ssh_key, sshkey_get.name)

    def test026_sshkey_get_with_non_exist_name(self):
        """
        TC 665
        test case to check sshkey_get method with wrong name, should fail.

        **Test scenario**
        #. get the sshkey with wrong name.
        #. check that the command raises an error.
        """
        self.info("get the sshkey with DOESNT_EXIST ssh key, it should raise an error")
        with self.assertRaises(Exception):
            self.DO_CLIENT.sshkey_get(name="DOESNT_EXIST")

    def test027_region_get_with_exist_name(self):
        """
        TC 666
        test case to check region_get method with ams3 name

        **Test scenario**
        #. check the existence of region called ams3.
        #. check that the command is executed without any error, and the region name equal to 'Amsterdam 3'.
        """
        self.info("get the region with name ams3")
        region = self.DO_CLIENT.region_get("ams3")
        self.info("check that the command is executed without any error")
        self.assertTrue(region)
        self.info("the region name equal to 'Amsterdam 3'")
        self.assertEqual('Amsterdam 3', region.name)

    def test028_region_get_with_non_exist_name(self):
        """
        TC 667
        test case to check region_get with wrong name, should fail.

        **Test scenario**
        #. get the region with wrong name.
        #. check that the command raises an error.
        """
        self.info("get the region with DOESNT_EXIST name, it should raise an error")
        with self.assertRaises(Exception):
            self.DO_CLIENT.region_get("DOESNT_EXIST")

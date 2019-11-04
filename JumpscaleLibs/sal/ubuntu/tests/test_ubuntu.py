from JumpscaleLibs.sal.ubuntu.Ubuntu import Ubuntu
from Jumpscale import j
from unittest import TestCase
import os
import time
from unittest import skip
from loguru import logger


class Test_Ubuntu(TestCase):
    j.sal.process.execute("apt update -y")
    j.sal.process.execute("apt-get install -y python3-distutils-extra python3-dbus python3-apt")

    LOGGER = logger
    LOGGER.add("Config_manager_{time}.log")

    @staticmethod
    def info(message):
        Test_Ubuntu.LOGGER.info(message)

    def _check_init_process(self):
        process = j.sal.process.getProcessObject(1)
        name = process.name()
        if not name == "my_init" and not name == "systemd":
            raise j.exceptions.RuntimeError("Unsupported init system process")

        return name

    def setUp(self):
        self.ubuntu = Ubuntu()

    def tearDown(self):
        pass

    def test001_uptime(self):
        """TC395
        check ubuntu uptime

        **Test Scenario**
        #. Check uptime from system file located at  /proc/uptime
        #. Compare it with tested method ubuntu.uptime()
        #. Both uptime from system file and from method are almost equal
        """
        self.info("verfying uptime method")
        with open("/proc/uptime") as f:
            data = f.read()
            uptime, _ = data.split(" ")
        self.assertAlmostEqual(float(uptime), self.ubuntu.uptime(), delta=2)

    def test002_service_install(self):

        """TC396
        service_install is not a package install which is mean only create a config file in /etc/init/ dir

        **Test Scenario**
        #. Let take a zdb as out tested service , check the zdb config file existing
        #. Check if the service config file is exist, then we need to uninstall service to verify tested method \
        service install works well
        #. Install zdb service by tested method
        #. Verify that config file existing after enable the service
        #. Uninstall service to return to origin state
        #. if the service config file was exist then we need install service again to return to origin state
        """
        mysys = None
        zdb_service_file = False
        self.info("installing zdb for testing")
        j.builders.db.zdb.install()
        self.info("checking system is systemd or not ")
        mysys = self._check_init_process()
        if mysys == "my_init":
            self.info("system is init system")
            zdb_service_file = os.path.exists("/etc/service/zdb/run")
        elif mysys == "systemd":
            self.info("system is init systemd")
            zdb_service_file = os.path.exists("/etc/systemd/system/zdb.service")
        else:
            self.info("something unexpected occurred while checking system type")
            self.assertIn(mysys, ["systemd", "my_init"], "system not supported ")

        self.info("checking zdb file existing ")
        if zdb_service_file is True:
            self.info("zdb file is exist ,service_uninstall to zdb service ")
            self.ubuntu.service_uninstall("zdb")
        self.info("service_install to zdb service ")
        self.ubuntu.service_install("zdb", "/sandbox/bin")
        self.info("Verify config file existing after using service_install")
        if mysys == "my_init":
            self.assertTrue(os.path.exists("/etc/service/zdb/run"))
        else:
            self.assertTrue(os.path.exists("/etc/systemd/system/zdb.service"))
        self.info("zdb service uninstall to return to origin state")
        self.ubuntu.service_uninstall("zdb")
        if zdb_service_file is True:
            self.info("zdb service install to return to origin state")
            self.ubuntu.service_install("zdb", "/sandbox/zdb")

    def test003_version_get(self):
        """TC398
        Check the ubuntu version

        **Test Scenario**
        #. Check Ubuntu version using tested method ubuntu.version_get
        #. Verify step1 output include keyword Ubuntu
        """
        self.info("checking ubuntu version ")
        self.assertIn("Ubuntu", self.ubuntu.version_get())

    def test004_apt_install_check(self):
        """TC399
        check if an ubuntu package is installed or not installed will install it

        **Test Scenario**
        #. Just run method and if it fails, it will raise an error
        """
        self.info("checking ping is installed or not ")
        self.ubuntu.apt_install_check("iputils-ping", "ping")
        with self.assertRaises(Exception) as myexcept:
            self.ubuntu.apt_install_check("iputils-ping", "elfankosh")
            self.info("There is exceptions RuntimeError due to elfankosh is not a command")
            self.assertIn("Could not execute: 'which elfankosh'", myexcept.exception.args[0])

    def test005_apt_install_version(self):
        """TC400
        Install a specific version of an ubuntu package.

        **Test Scenario**
        #. Install wget package using apt_install_version method
        #. check version of wget after installing it
        #. step1 and step2 should be identical
        :return:
        """
        wget_installed = False
        wget_installed = self.ubuntu.is_pkg_installed("wget")
        self.info("print wget install var is {}".format(wget_installed))
        if wget_installed is True:
            self.info("uninstall wget to test install method  ")
        self.info("installing wget with version 1.19.4")
        self.ubuntu.apt_install_version("wget", "1.19.4-1ubuntu2.2")
        self.info("checking installed wget version ")
        rc, out, err = j.sal.process.execute("wget -V", useShell=True)
        self.info("verifying installed wget version is 1.19.4")
        self.assertIn("1.19.4", out)
        self.info("removing wget to get back to origin state")
        j.sal.process.execute("apt remove -y wget")
        if wget_installed is True:
            self.info("uninstall wget and install default version from ubuntu repo")
            j.sal.process.execute("apt install -y wget")

    def test006_deb_install(self):
        """TC402
        Install a debian package.

        **Test Scenario**
        #. Download python-tmuxp debian package
        #. Install downloaded debian package by deb_install method
        #. Get the installed package status by dpkg command
        #. Installed package python-tmuxp should be install ok
        """
        self.info("Downloading python-tmuxp debian package")
        j.sal.process.execute(
            "curl  http://security.ubuntu.com/ubuntu/pool/universe/t/tmuxp/python-tmuxp_1.5.0a-1_all.deb > python-tmuxp_1.5.0a-1_all.deb"
        )
        self.info("Install downloaded debian package by deb_install method")
        self.ubuntu.deb_install(path="python-tmuxp_1.5.0a-1_all.deb")
        self.info("Get the installed package status by dpkg command")
        rc, out, err = j.sal.process.execute("dpkg -s python-tmuxp | grep Status", die=False)
        self.info("Installed package python-tmuxp should be install ok")
        self.assertIn("install ok", out)

    def test007_pkg_list(self):

        """TC403
        list files of dpkg.

        **Test Scenario**
        # . no package called ping so output len should equal zero\
        the correct package name is iputils-ping
        """
        self.info("verifying that pkg_list equal zero as no dpkg called ping, it should be iputils-ping")
        self.assertEqual(len(self.ubuntu.pkg_list("ping")), 0)
        self.assertGreaterEqual(len(self.ubuntu.pkg_list("iputils-ping")), 1)

    def test008_service_start(self):
        """TC404
        start an ubuntu service.

        **Test Scenario**
        #. Check cron status before testing service_start method
        #. If status of cron is running then stop cron service so we can test service_start method
        #. Start cron service using start_service method
        #. Check the corn status by service_status method
        #. As it was running before test,starting cron service after finishing testing by service_start method
        """
        cront_status = False
        self.info("check cron status before testing service_start method ")
        cront_status = self.ubuntu.service_status("cron")
        if cront_status is True:
            self.info("stopping cron service so we can test service_start method")
            self.ubuntu.service_stop("cron")
        self.info("Start cron service using start_service method ")
        self.ubuntu.service_start("cron")
        self.info("check the corn status by service_status method")
        self.info("status of service is {} ".format(self.ubuntu.service_status("cron")))
        self.assertTrue(self.ubuntu.service_status("cron"))

    def test009_service_stop(self):
        """TC405
        stop an ubuntu service.

        **Test Scenario**
        #. Check cron status before testing service_stop method
        #. If status of cron is not running then start before test service_stop method
        #. Service should be running, stopping cron service using tested method service_stop
        #. Get the service status by service_status method should be False
        #. Retrun cron service status as origin state to be running
        #. Stop cron service to be as origin state
        """
        cront_status = False
        self.info("check cron status before testing service_stop method ")
        cront_status = self.ubuntu.service_status("cron")
        if cront_status is False:
            self.info("status was stopped before test method we need to start it now and stop it after finish test")
            self.ubuntu.service_start("cron")
        self.info("service should be running, stopping cron service using tested method service_stop")
        self.ubuntu.service_stop("cron")
        self.info("Get the service status by service_status method should be False ")
        self.assertFalse(self.ubuntu.service_status("cron"))
        self.info("Retrun cron service status as origin state to be running ")
        self.ubuntu.service_start("cron")
        if cront_status is False:
            self.info("stop cron service to be as origin state")
            self.ubuntu.service_stop("cron")

    def test010_service_restart(self):
        """TC406
        restart an ubuntu service.

        **Test Scenario**
        #. Check cron status before testing service_start method
        #. If status of cron is running then stop cron service so we can test service_start method
        #. Restart cron service using start_service method
        #. Check the corn status by service_status method
        #. As it was running before test,starting cron service after finishing testing by service_start method
        """
        cront_status = False
        self.info("check cron status before testing service_start method ")
        cront_status = self.ubuntu.service_status("cron")
        if cront_status is True:
            self.info("stopping cron service so we can test service_start method")
            self.ubuntu.service_stop("cron")
        self.info("restart cron service using start_service method ")
        self.ubuntu.service_restart("cron")
        self.info("check the corn status by service command")
        self.assertTrue(self.ubuntu.service_status("cron"))

    def test011_service_status(self):
        """TC407
        check service status

        **Test Scenario**
        #. Get service status
        #. if service is not running, verifying tested method return False
        #. else service is running, should return True
        """
        self.info("Get service status")
        state = self.ubuntu.service_status("cron")
        if state is False:
            self.info("service is not running, verifying tested method return False")
            self.assertFalse(self.ubuntu.service_status("cron"))
        else:
            self.info("service is running, verifying tested method should return True")
            self.assertTrue(self.ubuntu.service_status("cron"))

    def test012_apt_find_all(self):

        """TC408
        find all packages match with the package_name, this mean must not be installed

        **Test Scenario**
        #. alot if packages are containing wget like  'python3-wget', 'wget'
        """
        self.info("verifying all available packages have a keyword wget")
        self.assertIn("wget", self.ubuntu.apt_find_all("wget"))

    def test013_is_pkg_installed(self):
        """TC409
        check if the package is installed or not

        **Test Scenario**
        #. make sure wget installed successfully
        #. Install it if does not installed
        #. Verifying tested pkg_installed should return True as wget is installed
        #. Remove it to return to origin state
        """
        wget_is_installed = False
        self.info("make sure wget installed")
        rc1, out, err = j.sal.process.execute("dpkg -s wget|grep Status")
        if "deinstall ok" in out:
            self.info("install wget as it does not installed")
            j.sal.process.execute("apt install -y wget")
        self.info("verifying tested pkg_installed should return True as wget is installed")
        wget_is_installed = j.sal.ubuntu.is_pkg_installed("wget")
        self.info(" wget_is_installed is  {} ".format(wget_is_installed))
        self.assertTrue(wget_is_installed)
        if "install ok" not in out:
            self.info("Remove it to return to origin state")
            j.sal.process.execute("apt remove -y wget")

    def test014_sshkey_generate(self):
        """TC410
        generate a new ssh key

        **Test Scenario**
        #. Generate sshkey in path /tmp/id_rsa
        #. verify that there is a files, their names contain id_rsa
        """
        self.info("Generate sshkey in path /tmp/id_rsa")
        self.ubuntu.sshkey_generate(path="/tmp/id_rsa")
        self.info("verify that there is a files, their names contain id_rsa")
        rc, out, err = j.sal.process.execute("ls /tmp | grep id_rsa")
        self.assertIn("id_rsa", out)

    def test015_apt_get_cache_keys(self):
        """TC411
        get all cached packages of ubuntu

        **Test Scenario**
        #. Get all cached keys by our tested method apt_get_cache_keys
        #. Get a one package from cached packages by apt-cache command
        #. Compare the package name of step2 should be included in keys from step 1
        """
        self.info("Get all cached keys by our tested method apt_get_cache_keys")
        cache_list = self.ubuntu.apt_get_cache_keys()
        self.info(" Get a one package from cached packages by apt-cache command")
        rc1, pkg_name, err1 = j.sal.process.execute("apt-cache search 'Network' | head -1| awk '{print $1}'")
        name = pkg_name.strip()
        self.info("verify one package if cached packages forn apt-cache command should exist in tested method output")
        self.assertIn(name, cache_list)

    def test016_apt_get_installed(self):

        """TC412
        Get all the installed packages.

        **Test Scenario**
        #. Get length of installed packages from apt list command
        #. Get length of installed packages from tested method
        #. Compare step 1 and 2 should be equal\
        installed packages by tested method  and apt list command should be the same
        """
        sal_count = 0
        self.info("Get length of installed packages from apt list command ")
        rc1, os_count, err1 = j.sal.process.execute("apt list --installed |grep -v 'Listing...'| wc -l")
        os_int_count = int(os_count.strip())
        self.info("Get length of installed packages from tested method")
        sal_count = len(self.ubuntu.apt_get_installed())
        self.info("Verifying installed packages by tested method and apt list command should be the same")
        self.assertEqual(sal_count, os_int_count)

    def test017_apt_install(self):
        """TC413
        install a specific ubuntu package.

        **Test Scenario**
        #. Check if speedtest-cli is installed or not
        #. if installed, remove it and use tested method to install it and verify that is installed
        #. else we install speedtest-cli by tested method
        #. verify that is installed successfully
        #. remove it to be as origin status
        """
        self.info("Check if speedtest-cli is installed or not")
        speedtest_installed = j.sal.ubuntu.is_pkg_installed("speedtest-cli")
        if speedtest_installed:
            self.info("remove speedtest-cli package")
            j.sal.process.execute("apt remove -y speedtest-cli")
        self.info("install speedtest-cli package")
        self.ubuntu.apt_install("speedtest-cli")
        self.info("verify that speedtest-cli is installed")
        rc1, out1, err1 = j.sal.process.execute("dpkg -s speedtest-cli|grep Status")
        self.assertIn("install ok", out1)
        if not speedtest_installed:
            self.info("remove it speedtest-cli to be as origin status")
            j.sal.process.execute("apt remove -y speedtest-cli")

    def test018_apt_sources_list(self):
        """TC414
        represents the full sources.list + sources.list.d file

        **Test Scenario**
        #. Get all listed apt sources by tested method apt_sources_list
        #. Get the first line in apt sources list
        #. Verify first item should contains a keyword deb
        """
        self.info("Get all listed apt sources by tested method apt_sources_list")
        apt_src_list = self.ubuntu.apt_sources_list()
        self.info("Get the first line in apt sources list")
        first_src = apt_src_list[0]
        self.info("Verify first item should contains a keyword deb")
        self.assertIn("deb", first_src)

    def test019_apt_sources_uri_add(self):
        """TC415
        add a new apt source url.

        **Test Scenario**
        #. Check if the source link file that am gonna add it exist or not
        #. file exist move it a /tmp dir
        #. Adding new url to apt sources
        #. Check contents of added file under /etc/apt/sources.list.d
        #. Verify file contents are contains deb keyword
        #. Remove created file by tested method
        #. if file was exist in step 1 , move the backup file from /tmp to origin path
        """
        self.info("check if the source link file that am gonna add it exist or not")
        file_exist = os.path.exists("/etc/apt/sources.list.d/archive.getdeb.net.list")
        if file_exist:
            self.info("file exist move it a /tmp dir")
            j.sal.process.execute("mv /etc/apt/sources.list.d/archive.getdeb.net.list /tmp")
        self.info("adding new url to apt sources ")
        self.ubuntu.apt_sources_uri_add("http://archive.getdeb.net/ubuntu wily-getdeb games")
        self.info("check contents of added file under /etc/apt/sources.list.d")
        rc1, os_apt_sources, err1 = j.sal.process.execute(
            "grep 'ubuntu wily-getdeb games' /etc/apt/sources.list.d/archive.getdeb.net.list"
        )
        self.info("verify file contents are contains deb keyword")
        self.assertIn("deb", os_apt_sources)
        self.info("remove created file by tested method")
        j.sal.process.execute("rm /etc/apt/sources.list.d/archive.getdeb.net.list")
        if file_exist:
            self.info("move the backuped file from /tmp to origin path")
            j.sal.process.execute("mv /tmp/archive.getdeb.net.list /etc/apt/sources.list.d/")

    def test020_apt_upgrade(self):
        """TC416
        upgrade is used to install the newest versions of all packages currently installed on the system

        **Test Scenario**
        #. Get number of packages that need to be upgraded
        #. Run tested method to upgrade packages
        #. Get number of packages that need to be upgraded again after upgrade
        #. if upgrade runs successfully then number in step 1 should be greater than one in step3
        #. comparing the count of packages need to be upgraded before and after upgarde
        #. if all packages are already upgraded before run our tested method and no need to upgrade any packages\
        they should be equal so i used GreaterEqual
        """
        self.info("Get number of packages that need to be upgraded")
        rc1, upgradable_pack_before_upgrade, err1 = j.sal.process.execute(
            "apt list --upgradable | grep -v 'Listing...'| wc -l"
        )
        upgradable_pack_count_before_upgrade = int(upgradable_pack_before_upgrade.strip())
        self.info("Run tested method to upgrade packages")
        self.ubuntu.apt_upgrade()
        self.info("Get number of packages that need to be upgraded again after upgrade")
        rc2, upgradable_pack_after_upgrade, err2 = j.sal.process.execute(
            "apt list --upgradable | grep -v 'Listing...'| wc -l"
        )
        upgradable_pack_count_after_upgrade = int(upgradable_pack_after_upgrade.strip())
        self.info("comparing the count of packages need to be upgraded before and after upgarde ")
        self.assertGreaterEqual(upgradable_pack_count_before_upgrade, upgradable_pack_count_after_upgrade)

    def test021_check_os(self):
        """TC417
        check is True when the destribution is ubunut or linuxmint

        **Test Scenario**
        #. Get os name by lsb_release command
        #. Get release number (version) by lsb_release command
        #. Check OS name should be between "Ubuntu", "LinuxMint"
        #. if OS is Ubuntu or LinuxMint, checking version should be greater than 14
        #. if OS is not Ubuntu or LinuxMint, exceptions RuntimeError gonna appear as Only Ubuntu/Mint supported
        #. if OS version (number) is greater than 14, verifying tested method should return True
        #. if OS version (number) is less than 14, RuntimeError gonna appear as Only ubuntu version 14+ supported
        """

        self.info("Get os name by lsb_release command")
        rc1, distro_name, err1 = j.sal.process.execute("lsb_release -i | awk '{print $3}'")
        distro1 = distro_name.strip()
        self.info("Get release number (version) by lsb_release command")
        rc2, out2, err2 = j.sal.process.execute("lsb_release -r|awk '{print $2}'")
        distrbo_num = out2.strip()
        release_num = float(distrbo_num)
        self.info("Check OS name should be between Ubuntu or LinuxMint")
        if distro1 in ("Ubuntu", "LinuxMint"):
            self.info("OS is Ubuntu or LinuxMint, checking version should be greater than 14")
            if release_num > 14:
                self.info("verifying tested method should return True")
                self.assertTrue(self.ubuntu.check())
            else:
                with self.assertRaises(j.exceptions.RuntimeError) as myexcept:
                    self.ubuntu.check()
                    self.info("There is exceptions RuntimeError as Only ubuntu version 14+ supported")
                    self.assertIn("Only ubuntu version 14+ supported", myexcept.exception.args[0])
        else:
            with self.assertRaises(j.exceptions.RuntimeError) as e:
                self.ubuntu.check()
                self.info("There is exceptions RuntimeError as the OS is not between Ubuntu or LinuxMint")
                self.assertIn("Only Ubuntu/Mint supported", e.exception.args[0])

    def test022_deb_download_install(self):
        """TC418
        check download and install the package

        **Test Scenario**
        #. Check status of tcpdump is installed or not
        #. If tcpdump installed remove it by apt remove before install it
        #. Installed it again by tested method
        #. Get tcpdump status should be installed successfully
        #. Verify that tcpdump installed successfully
        #. Remove tcpdump to return to origin state
        #. Install tcpdump to return to origin state as we remove it before testing
        """
        self.info("Check status of tcpdump is installed or not")
        tcpdump_installed = j.sal.ubuntu.is_pkg_installed("tcpdump")
        if tcpdump_installed:
            self.info("tcpdump is installed, removing it")
            j.sal.process.execute("apt remove -y tcpdump")
        self.info("installed tcpdump again by tested method")
        j.sal.ubuntu.deb_download_install(
            "http://download.unesp.br/linux/debian/pool/main/t/tcpdump/tcpdump_4.9.2-3_amd64.deb"
        )
        self.info("Get tcpdump status should be installed successfully ")
        rc2, out2, err2 = j.sal.process.execute("dpkg -s tcpdump|grep Status")
        self.info("verify that tcpdump installed successfully")
        self.assertIn("install ok", out2)
        self.info("remove tcpdump to return to origin state")
        j.sal.process.execute("apt remove -y tcpdump")
        if tcpdump_installed:
            self.info("install tcpdump to return to origin state as we remove it before testing ")
            j.sal.process.execute("apt install -y tcpdump")

    def test023_pkg_remove(self):
        """TC419
        remove an ubuntu package.

        **Test Scenario**
        #. Check the tcpdummp is installed or not
        #. If tcpdump not installed, install it manually
        #. Remove tcpdump by tested method pkg_remove
        #. Verify package has been removed by tested method
        #. Remove tcpdump to return to origin state
        """
        self.info("Check the tcpdump is installed or not")
        tcpdump_already_installed = j.sal.ubuntu.is_pkg_installed("tcpdump")
        if not tcpdump_already_installed:
            self.info("tcpdump not installed, installing it ")
            j.sal.process.execute("apt install -y tcpdump")
        self.info("remove tcpdump by tested method pkg_remove")
        j.sal.ubuntu.pkg_remove("tcpdump")
        self.info("verify package has been removed by tested method")
        self.assertFalse(j.sal.ubuntu.is_pkg_installed("tcpdump"))
        if not tcpdump_already_installed:
            self.info("remove tcpdump to return to origin state")
            j.sal.process.execute("apt remove -y tcpdump")

    def test024_service_disable_start_boot(self):
        """TC420
        remove all links are named as /etc/rcrunlevel.d/[SK]NNname that point to the script /etc/init.d/name.

        **Test Scenario**
        #. Check cron file link exist or not
        #. If file does not exist, enable service so file will created
        #. Disable cron service by using tested method service_disable_start_boot
        #. Verify that file does not exist after disable cron service
        #. Enable cron service to create service file to return as origin state
        #. Disable cron service as cron service does not exist before testing to return back to origin state
        """
        self.info("check cron file link exist or not ")
        cron_file_exist = os.path.exists("/etc/rc5.d/S01cron")
        if not cron_file_exist:
            self.info("file does not exist, enable service so file will created")
            self.ubuntu.service_enable_start_boot("cron")
        self.info("disable cron service by using tested method service_disable_start_boot ")
        self.ubuntu.service_disable_start_boot("cron")
        self.info("verify that file does not exist after disable cron service")
        self.assertFalse(os.path.exists("/etc/rc5.d/S01cron"))
        self.info("enable cron service to create service file to return as origin state")
        self.ubuntu.service_enable_start_boot("cron")
        if not cron_file_exist:
            self.info(
                "disable cron service as cron service does not exist before testing to return back to origin state"
            )
            self.ubuntu.service_disable_start_boot("cron")

    def test025_service_enable_start_boot(self):
        """TC421
        it makes links named /etc/rcrunlevel.d/[SK]NNname that point to the script /etc/init.d/name.

        **Test Scenario**
        #. Check cron file link exist or not
        #. If file exist,backup service file to /tmp before disabling it
        #. Disable service at boot
        #. Verify that file does not eixst after disabling service
        #. Enable service at boot again to check tested method
        #. Verify cron file is exist after enabling service
        #. Return back the backup file to origin path
        """
        self.info("check cron file link exist or not ")
        cron_file_exist = os.path.exists("/etc/rc5.d/S01cron")
        if cron_file_exist:
            self.info("file exist,backup service file to /tmp before disabling it")
            j.sal.process.execute("cp /etc/rc5.d/S01cron /tmp")
            self.info("disable service at boot")
            self.ubuntu.service_disable_start_boot("cron")
            self.info("Verify that file does not eixst after disabling service ")
            self.assertFalse(os.path.exists("/etc/rc5.d/S01cron"))
        self.info("enable service at boot again to check tested method ")
        self.ubuntu.service_enable_start_boot("cron")
        self.info("Verify cron file is exist after enabling service")
        self.assertTrue(os.path.exists("/etc/rc5.d/S01cron"))
        if cron_file_exist:
            self.info("retrun back the backup file to origin path")
            j.sal.process.execute("cp /tmp/S01cron /etc/rc5.d/S01cron ")

    def test026_service_uninstall(self):
        """TC422
        remove an ubuntu service.

        **Test Scenario**
        #. Check cron service config file existing under /etc/init
        #. If ron service file config does not exist in /etc/ini, install service so config file will created
        #. Backup the config file to /tmp before testing
        #. Uninstall service to test tested method service_uninstall
        #. Verify the cron config file does not exist after uninstalling service
        #. Return back backup file to orgin path after testing
        #. If file was not exist, remove service config file to return back to origin state
        """
        mysys = None
        zdb_service_file = False
        self.info("installing zdb from builder")
        j.builders.db.zdb.install()
        self.info("checking system is systemd or not ")
        mysys = self._check_init_process()
        if mysys == "my_init":
            self.info("system is init system")
            zdb_service_file = os.path.exists("/etc/service/zdb/run")
        elif mysys == "systemd":
            self.info("system is init systemd")
            zdb_service_file = os.path.exists("/etc/systemd/system/zdb.service")
        else:
            self.info("something unexpected occurred while checking system type")
            self.assertIn(mysys, ["systemd", "my_init"], "system not supported ")
        if zdb_service_file is False:
            self.info("zdb service file config does not exist, install service so config file will created ")
            self.ubuntu.service_install("zdb", "/sandbox/bin")
        self.info("backup the config file to /tmp before testing ")
        if mysys == "my_init":
            j.sal.process.execute("cp /etc/service/zdb/run /tmp/run_zdb")
        else:
            j.sal.process.execute("cp /etc/systemd/system/zdb.service /tmp")

        self.info("uninstall service to test tested method service_uninstall")
        self.ubuntu.service_uninstall("zdb")
        self.info("Verify the zdb config file does not exist after uninstalling service ")
        if mysys == "my_init":
            self.assertFalse(os.path.exists("/etc/service/zdb/run"))
        else:
            self.assertFalse(os.path.exists("/etc/systemd/system/zdb.service"))
        self.info("return back backup file to orgin path after testing ")
        if mysys == "my_init":
            j.sal.process.execute("cp /tmp/run_zdb /etc/service/zdb/run ")
        else:
            j.sal.process.execute("cp /tmp/zdb.service /etc/systemd/system/zdb.service ")
        if zdb_service_file is False:
            self.info("remove service config file to return back to origin state")
            if mysys == "my_init":
                j.sal.process.execute("rm /etc/service/zdb/run")
            else:
                j.sal.process.execute("rm /etc/systemd/system/zdb.service")

    def test027_whoami(self):
        """TC397
        check current login user

        **Test Scenario**
        #. Check whoami method output
        #. Check os current user by using command whoami
        #. Comapre step1 and step2, should be identical

        """
        self.info("checking whoami method output")
        sal_user = self.ubuntu.whoami()
        self.info("checking OS whoami command output")
        rc2, os_user, err2 = j.sal.process.execute("whoami")
        self.info("comparing  whoami method output vs OS whoami command output")
        self.assertEquals(os_user.strip(), sal_user)


def main(self=None):
    """
    to run:
    kosmos 'j.sal.ubuntu._test(name="ubuntu")'
    """
    test_ubuntu = Test_Ubuntu()
    test_ubuntu.setUp()
    test_ubuntu.test001_uptime()
    test_ubuntu.test002_service_install()
    test_ubuntu.test003_version_get()
    test_ubuntu.test004_apt_install_check()
    test_ubuntu.test005_apt_install_version()
    test_ubuntu.test006_deb_install()
    test_ubuntu.test007_pkg_list()
    test_ubuntu.test008_service_start()
    test_ubuntu.test009_service_stop()
    test_ubuntu.test010_service_restart()
    test_ubuntu.test011_service_status()
    test_ubuntu.test012_apt_find_all()
    test_ubuntu.test013_is_pkg_installed()
    test_ubuntu.test014_sshkey_generate()
    test_ubuntu.test015_apt_get_cache_keys()
    test_ubuntu.test016_apt_get_installed()
    test_ubuntu.test017_apt_install()
    test_ubuntu.test018_apt_sources_list()
    test_ubuntu.test019_apt_sources_uri_add()
    test_ubuntu.test020_apt_upgrade()
    test_ubuntu.test021_check_os()
    test_ubuntu.test022_deb_download_install()
    test_ubuntu.test023_pkg_remove()
    test_ubuntu.test024_service_disable_start_boot()
    test_ubuntu.test025_service_enable_start_boot()
    test_ubuntu.test026_service_uninstall()
    test_ubuntu.test027_whoami()
    test_ubuntu.tearDown()

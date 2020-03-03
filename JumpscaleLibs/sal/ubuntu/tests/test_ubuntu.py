import os
from math import isclose
from Jumpscale import j
try:
    from loguru import logger
except ImportError:
    j.builders.runtimes.python3.pip_package_install("loguru", reset=True)
    from loguru import logger


"""
j.sal.ubuntu._test(name='ubuntu')
"""

j.sal.process.execute("apt update -y")
try:
    j.sal.process.execute("apt-get install -y python3-distutils-extra python3-dbus python3-apt")
except:
    j.sal.process.execute("apt-get install -y python3-dbus python3-apt")

skip = j.baseclasses.testtools._skip


def info(message):
    j.tools.logger._log_info(message)


def _check_init_process():
    process = j.sal.process.getProcessObject(1)
    name = process.name()
    if not name == "my_init" and not name == "systemd":
        raise j.exceptions.RuntimeError("Unsupported init system process")

    return name


ubuntu = ""


def before():
    global ubuntu
    ubuntu = j.sal.ubuntu


def test001_uptime():
    """TC395
    check ubuntu uptime

    **Test Scenario**
    #. Check uptime from system file located at  /proc/uptime
    #. Compare it with tested method ubuntu.uptime()
    #. Both uptime from system file and from method are almost equal
    """
    info("verfying uptime method")
    with open("/proc/uptime") as f:
        data = f.read()
        uptime, _ = data.split(" ")
    assert isclose(float(uptime), j.sal.ubuntu.uptime(), abs_tol=2)


def test002_service_install():
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
    info("installing zdb for testing")
    j.builders.db.zdb.install()
    info("checking system is systemd or not ")
    mysys = _check_init_process()
    if mysys == "my_init":
        info("system is init system")
        zdb_service_file = os.path.exists("/etc/service/zdb/run")
    elif mysys == "systemd":
        info("system is init systemd")
        zdb_service_file = os.path.exists("/etc/systemd/system/zdb.service")
    else:
        info("something unexpected occurred while checking system type")
        assert mysys in ["systemd", "my_init"], "system not supported "

    info("checking zdb file existing ")
    if zdb_service_file is True:
        info("zdb file is exist ,service_uninstall to zdb service ")
        j.sal.ubuntu.service_uninstall("zdb")
    info("service_install to zdb service ")
    j.sal.ubuntu.service_install("zdb", j.core.tools.text_replace("{DIR_BASE}/bin"))
    info("Verify config file existing after using service_install")
    if mysys == "my_init":
        assert os.path.exists("/etc/service/zdb/run")
    else:
        assert os.path.exists("/etc/systemd/system/zdb.service")
    info("zdb service uninstall to return to origin state")
    j.sal.ubuntu.service_uninstall("zdb")
    if zdb_service_file is True:
        info("zdb service install to return to origin state")
        j.sal.ubuntu.service_install("zdb", j.core.tools.text_replace("{DIR_BASE}/zdb"))


def test003_version_get():
    """TC398
    Check the ubuntu version

    **Test Scenario**
    #. Check Ubuntu version using tested method ubuntu.version_get
    #. Verify step1 output include keyword Ubuntu
    """
    info("checking ubuntu version ")
    assert "Ubuntu" in j.sal.ubuntu.version_get()


def test004_apt_install_check():
    """TC399
    check if an ubuntu package is installed or not installed will install it

    **Test Scenario**
    #. Just run method and if it fails, it will raise an error
    """
    info("checking ping is installed or not ")
    j.sal.ubuntu.apt_install_check("iputils-ping", "ping")
    try:
        j.sal.ubuntu.apt_install_check("iputils-ping", "elfankosh")
        info("There is exceptions RuntimeError due to elfankosh is not a command")
    except Exception as myexcept:
        assert "Could not execute: 'which elfankosh'" in myexcept.exception.args[0]


def test005_apt_install_version():
    """TC400
    Install a specific version of an ubuntu package.

    **Test Scenario**
    #. Install wget package using apt_install_version method
    #. check version of wget after installing it
    #. step1 and step2 should be identical
    :return:
    """
    wget_installed = False
    wget_installed = j.sal.ubuntu.is_pkg_installed("wget")
    info("print wget install var is {}".format(wget_installed))
    if wget_installed is True:
        info("uninstall wget to test install method  ")
    info("installing wget with version 1.19.4")
    j.sal.ubuntu.apt_install_version("wget", "1.19.4-1ubuntu2")
    info("checking installed wget version ")
    rc, out, err = j.sal.process.execute("wget -V", useShell=True)
    info("verifying installed wget version is 1.19.4")
    assert "1.19.4" in out
    info("removing wget to get back to origin state")
    j.sal.process.execute("apt remove -y wget")
    if wget_installed is True:
        info("uninstall wget and install default version from ubuntu repo")
        j.sal.process.execute("apt install -y wget")


def test006_deb_install():
    """TC402
    Install a debian package.

    **Test Scenario**
    #. Download python-tmuxp debian package
    #. Install downloaded debian package by deb_install method
    #. Get the installed package status by dpkg command
    #. Installed package python-tmuxp should be install ok
    """
    info("Downloading python-tmuxp debian package")
    j.sal.process.execute(
        "curl  http://security.ubuntu.com/ubuntu/pool/universe/t/tmuxp/python-tmuxp_1.5.0a-1_all.deb > python-tmuxp_1.5.0a-1_all.deb"
    )
    info("Install downloaded debian package by deb_install method")
    j.sal.ubuntu.deb_install(path="python-tmuxp_1.5.0a-1_all.deb")
    info("Get the installed package status by dpkg command")
    rc, out, err = j.sal.process.execute("dpkg -s python-tmuxp | grep Status", die=False)
    info("Installed package python-tmuxp should be install ok")
    assert "install ok" in out


def test007_pkg_list():
    """TC403
    list files of dpkg.

    **Test Scenario**
    # . no package called ping so output len should equal zero\
    the correct package name is iputils-ping
    """
    info("verifying that pkg_list equal zero as no dpkg called ping, it should be iputils-ping")
    assert len(j.sal.ubuntu.pkg_list("ping")) == 0
    assert len(j.sal.ubuntu.pkg_list("iputils-ping")) >= 1


def test008_service_start():
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
    info("check cron status before testing service_start method ")
    cront_status = j.sal.ubuntu.service_status("cron")
    if cront_status is True:
        info("stopping cron service so we can test service_start method")
        j.sal.ubuntu.service_stop("cron")
    info("Start cron service using start_service method ")
    j.sal.ubuntu.service_start("cron")
    info("check the corn status by service_status method")
    info("status of service is {} ".format(j.sal.ubuntu.service_status("cron")))
    assert j.sal.ubuntu.service_status("cron")


def test009_service_stop():
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
    info("check cron status before testing service_stop method ")
    cront_status = j.sal.ubuntu.service_status("cron")
    if cront_status is False:
        info("status was stopped before test method we need to start it now and stop it after finish test")
        j.sal.ubuntu.service_start("cron")
    info("service should be running, stopping cron service using tested method service_stop")
    j.sal.ubuntu.service_stop("cron")
    info("Get the service status by service_status method should be False ")
    assert j.sal.ubuntu.service_status("cron") is False
    info("Retrun cron service status as origin state to be running ")
    j.sal.ubuntu.service_start("cron")
    if cront_status is False:
        info("stop cron service to be as origin state")
        j.sal.ubuntu.service_stop("cron")


def test010_service_restart():
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
    info("check cron status before testing service_start method ")
    cront_status = j.sal.ubuntu.service_status("cron")
    if cront_status is True:
        info("stopping cron service so we can test service_start method")
        j.sal.ubuntu.service_stop("cron")
    info("restart cron service using start_service method ")
    j.sal.ubuntu.service_restart("cron")
    info("check the corn status by service command")
    assert j.sal.ubuntu.service_status("cron")


def test011_service_status():
    """TC407
    check service status

    **Test Scenario**
    #. Get service status
    #. if service is not running, verifying tested method return False
    #. else service is running, should return True
    """
    info("Get service status")
    state = j.sal.ubuntu.service_status("cron")
    if state is False:
        info("service is not running, verifying tested method return False")
        assert j.sal.ubuntu.service_status("cron") is False
    else:
        info("service is running, verifying tested method should return True")
        assert j.sal.ubuntu.service_status("cron")


def test012_apt_find_all():
    """TC408
    find all packages match with the package_name, this mean must not be installed

    **Test Scenario**
    #. alot if packages are containing wget like  'python3-wget', 'wget'
    """
    info("verifying all available packages have a keyword wget")
    assert "wget" in j.sal.ubuntu.apt_find_all("wget")


def test013_is_pkg_installed():
    """TC409
    check if the package is installed or not

    **Test Scenario**
    #. make sure wget installed successfully
    #. Install it if does not installed
    #. Verifying tested pkg_installed should return True as wget is installed
    #. Remove it to return to origin state
    """
    wget_is_installed = False
    info("make sure wget installed")
    rc1, out, err = j.sal.process.execute("dpkg -s wget|grep Status")
    if "deinstall ok" in out:
        info("install wget as it does not installed")
        j.sal.process.execute("apt install -y wget")
    info("verifying tested pkg_installed should return True as wget is installed")
    wget_is_installed = j.sal.ubuntu.is_pkg_installed("wget")
    info(" wget_is_installed is  {} ".format(wget_is_installed))
    assert wget_is_installed
    if "install ok" not in out:
        info("Remove it to return to origin state")
        j.sal.process.execute("apt remove -y wget")


def test014_sshkey_generate():
    """TC410
    generate a new ssh key

    **Test Scenario**
    #. Generate sshkey in path /tmp/id_rsa
    #. verify that there is a files, their names contain id_rsa
    """
    info("Generate sshkey in path /tmp/id_rsa")
    j.sal.ubuntu.sshkey_generate(path="/tmp/id_rsa")
    info("verify that there is a files, their names contain id_rsa")
    rc, out, err = j.sal.process.execute("ls /tmp | grep id_rsa")
    assert "id_rsa" in out


def test015_apt_get_cache_keys():
    """TC411
    get all cached packages of ubuntu

    **Test Scenario**
    #. Get all cached keys by our tested method apt_get_cache_keys
    #. Get a one package from cached packages by apt-cache command
    #. Compare the package name of step2 should be included in keys from step 1
    """
    info("Get all cached keys by our tested method apt_get_cache_keys")
    cache_list = j.sal.ubuntu.apt_get_cache_keys()
    info(" Get a one package from cached packages by apt-cache command")
    rc1, pkg_name, err1 = j.sal.process.execute("apt-cache search 'Network' | head -1| awk '{print $1}'")
    name = pkg_name.strip()
    info("verify one package if cached packages forn apt-cache command should exist in tested method output")
    assert name in cache_list


def test016_apt_get_installed():
    """TC412
    Get all the installed packages.

    **Test Scenario**
    #. Get length of installed packages from apt list command
    #. Get length of installed packages from tested method
    #. Compare step 1 and 2 should be equal\
    installed packages by tested method  and apt list command should be the same
    """
    sal_count = 0
    info("Get length of installed packages from apt list command ")
    rc1, os_count, err1 = j.sal.process.execute("apt list --installed |grep -v 'Listing...'| wc -l")
    os_int_count = int(os_count.strip())
    info("Get length of installed packages from tested method")
    sal_count = len(j.sal.ubuntu.apt_get_installed())
    info("Verifying installed packages by tested method and apt list command should be the same")
    assert sal_count == os_int_count


def test017_apt_install():
    """TC413
    install a specific ubuntu package.

    **Test Scenario**
    #. Check if speedtest-cli is installed or not
    #. if installed, remove it and use tested method to install it and verify that is installed
    #. else we install speedtest-cli by tested method
    #. verify that is installed successfully
    #. remove it to be as origin status
    """
    info("Check if speedtest-cli is installed or not")
    speedtest_installed = j.sal.ubuntu.is_pkg_installed("speedtest-cli")
    if speedtest_installed:
        info("remove speedtest-cli package")
        j.sal.process.execute("apt remove -y speedtest-cli")
    info("install speedtest-cli package")
    j.sal.ubuntu.apt_install("speedtest-cli")
    info("verify that speedtest-cli is installed")
    rc1, out1, err1 = j.sal.process.execute("dpkg -s speedtest-cli|grep Status")
    assert "install ok" in out1
    if not speedtest_installed:
        info("remove it speedtest-cli to be as origin status")
        j.sal.process.execute("apt remove -y speedtest-cli")


def test018_apt_sources_list():
    """TC414
    represents the full sources.list + sources.list.d file

    **Test Scenario**
    #. Get all listed apt sources by tested method apt_sources_list
    #. Get the first line in apt sources list
    #. Verify first item should contains a keyword deb
    """
    info("Get all listed apt sources by tested method apt_sources_list")
    apt_src_list = j.sal.ubuntu.apt_sources_list()
    info("Get the first line in apt sources list")
    first_src = apt_src_list[0]
    info("Verify first item should contains a keyword deb")
    assert "deb" in first_src


def test019_apt_sources_uri_add():
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
    info("check if the source link file that am gonna add it exist or not")
    file_exist = os.path.exists("/etc/apt/sources.list.d/archive.getdeb.net.list")
    if file_exist:
        info("file exist move it a /tmp dir")
        j.sal.process.execute("mv /etc/apt/sources.list.d/archive.getdeb.net.list /tmp")
    info("adding new url to apt sources ")
    j.sal.ubuntu.apt_sources_uri_add("http://archive.getdeb.net/ubuntu wily-getdeb games")
    info("check contents of added file under /etc/apt/sources.list.d")
    rc1, os_apt_sources, err1 = j.sal.process.execute(
        "grep 'ubuntu wily-getdeb games' /etc/apt/sources.list.d/archive.getdeb.net.list"
    )
    info("verify file contents are contains deb keyword")
    assert "deb" in os_apt_sources
    info("remove created file by tested method")
    j.sal.process.execute("rm /etc/apt/sources.list.d/archive.getdeb.net.list")
    if file_exist:
        info("move the backuped file from /tmp to origin path")
        j.sal.process.execute("mv /tmp/archive.getdeb.net.list /etc/apt/sources.list.d/")


def test020_apt_upgrade():
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
    info("Get number of packages that need to be upgraded")
    rc1, upgradable_pack_before_upgrade, err1 = j.sal.process.execute(
        "apt list --upgradable | grep -v 'Listing...'| wc -l"
    )
    upgradable_pack_count_before_upgrade = int(upgradable_pack_before_upgrade.strip())
    info("Run tested method to upgrade packages")
    j.sal.ubuntu.apt_upgrade()
    info("Get number of packages that need to be upgraded again after upgrade")
    rc2, upgradable_pack_after_upgrade, err2 = j.sal.process.execute(
        "apt list --upgradable | grep -v 'Listing...'| wc -l"
    )
    upgradable_pack_count_after_upgrade = int(upgradable_pack_after_upgrade.strip())
    info("comparing the count of packages need to be upgraded before and after upgarde ")
    assert upgradable_pack_count_before_upgrade >= upgradable_pack_count_after_upgrade


def test021_check_os():
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

    info("Get os name by lsb_release command")
    rc1, distro_name, err1 = j.sal.process.execute("lsb_release -i | awk '{print $3}'")
    distro1 = distro_name.strip()
    info("Get release number (version) by lsb_release command")
    rc2, out2, err2 = j.sal.process.execute("lsb_release -r|awk '{print $2}'")
    distrbo_num = out2.strip()
    release_num = float(distrbo_num)
    info("Check OS name should be between Ubuntu or LinuxMint")
    if distro1 in ("Ubuntu", "LinuxMint"):
        info("OS is Ubuntu or LinuxMint, checking version should be greater than 14")
        if release_num > 14:
            info("verifying tested method should return True")
            assert j.sal.ubuntu.check()
        else:
            try:
                j.sal.ubuntu.check()
                info("There is exceptions RuntimeError as Only ubuntu version 14+ supported")
            except (j.exceptions.RuntimeError) as myexcept:
                assert "Only ubuntu version 14+ supported" in myexcept.exception.args[0]
    else:
        try:
            j.sal.ubuntu.check()
            info("There is exceptions RuntimeError as the OS is not between Ubuntu or LinuxMint")
        except (j.exceptions.RuntimeError) as e:
            assert "Only Ubuntu/Mint supported" in e.exception.args[0]


def test022_deb_download_install():
    """TC418
        check download and install the package

        **Test Scenario**
        #. Check status of nano is installed or not
        #. If nano installed remove it by apt remove before install it
        #. Installed it again by tested method
        #. Get nano status should be installed successfully
        #. Verify that nano installed successfully
        #. Remove nano to return to origin state
        #. Install nano to return to origin state as we remove it before testing
        """
    info("Check status of nano: is installed or not")
    nano_installed = j.sal.ubuntu.is_pkg_installed("nano")
    if nano_installed:
        info("nano is installed, removing it")
        j.sal.process.execute("apt remove -y nano")
    info("installed nano again by tested method")
    j.sal.ubuntu.deb_download_install(
        "http://archive.ubuntu.com/ubuntu/pool/main/n/nano/nano_2.9.3-2_amd64.deb",
        remove_downloaded=True,
    )
    info("Get nano status should be installed successfully ")
    rc2, out2, err2 = j.sal.process.execute("dpkg -s nano|grep Status")
    info("verify that nano installed successfully")
    assert "install ok" in out2
    info("remove nano to return to origin state")
    j.sal.process.execute("apt remove -y nano")
    if nano_installed:
        info("install nano to return to origin state as we remove it before testing ")
        j.sal.process.execute("apt install -y nano")

# def test022_deb_download_install():
#     """TC418
#     check download and install the package
#
#     **Test Scenario**
#     #. Check status of vim-gtk is installed or not
#     #. If vim-gtk installed remove it by apt remove before install it
#     #. Installed it again by tested method
#     #. Get vim-gtk status should be installed successfully
#     #. Verify that vim-gtk installed successfully
#     #. Remove vim-gtk to return to origin state
#     #. Install vim-gtk to return to origin state as we remove it before testing
#     """
#     info("Check status of vim-gtk: is installed or not")
#     vim_gtk_installed = j.sal.ubuntu.is_pkg_installed("vim-gtk")
#     if vim_gtk_installed:
#         info("vim-gtk is installed, removing it")
#         j.sal.process.execute("apt remove -y vim-gtk")
#     info("installed vim-gtk again by tested method")
#     j.sal.ubuntu.deb_download_install(
#         "http://security.ubuntu.com/ubuntu/pool/universe/v/vim/vim-gtk_8.0.1453-1ubuntu1.1_amd64.deb",
#         remove_downloaded=True,
#     )
#     info("Get vim-gtk status should be installed successfully ")
#     rc2, out2, err2 = j.sal.process.execute("dpkg -s vim-gtk|grep Status")
#     info("verify that vim-gtk installed successfully")
#     assert "install ok" in out2
#     info("remove vim-gtk to return to origin state")
#     j.sal.process.execute("apt remove -y vim-gtk")
#     if vim_gtk_installed:
#         info("install vim-gtk to return to origin state as we remove it before testing ")
#         j.sal.process.execute("apt install -y vim-gtk")


def test023_pkg_remove():
    """TC419
    remove an ubuntu package.

    **Test Scenario**
    #. Check the tcpdummp is installed or not
    #. If tcpdump not installed, install it manually
    #. Remove tcpdump by tested method pkg_remove
    #. Verify package has been removed by tested method
    #. Remove tcpdump to return to origin state
    """
    info("Check the tcpdump is installed or not")
    tcpdump_already_installed = j.sal.ubuntu.is_pkg_installed("tcpdump")
    if not tcpdump_already_installed:
        info("tcpdump not installed, installing it ")
        j.sal.process.execute("apt install -y tcpdump")
    info("remove tcpdump by tested method pkg_remove")
    j.sal.ubuntu.pkg_remove("tcpdump")
    info("verify package has been removed by tested method")
    assert j.sal.ubuntu.is_pkg_installed("tcpdump") is False
    if not tcpdump_already_installed:
        info("remove tcpdump to return to origin state")
        j.sal.process.execute("apt remove -y tcpdump")


def test024_service_disable_start_boot():
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
    info("check cron file link exist or not ")
    cron_file_exist = os.path.exists("/etc/rc5.d/S01cron")
    if not cron_file_exist:
        info("file does not exist, enable service so file will created")
        j.sal.ubuntu.service_enable_start_boot("cron")
    info("disable cron service by using tested method service_disable_start_boot ")
    j.sal.ubuntu.service_disable_start_boot("cron")
    info("verify that file does not exist after disable cron service")
    assert os.path.exists("/etc/rc5.d/S01cron") is False
    info("enable cron service to create service file to return as origin state")
    j.sal.ubuntu.service_enable_start_boot("cron")
    if not cron_file_exist:
        info("disable cron service as cron service does not exist before testing to return back to origin state")
        j.sal.ubuntu.service_disable_start_boot("cron")


def test025_service_enable_start_boot():
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
    info("check cron file link exist or not ")
    cron_file_exist = os.path.exists("/etc/rc5.d/S01cron")
    if cron_file_exist:
        info("file exist,backup service file to /tmp before disabling it")
        j.sal.process.execute("cp /etc/rc5.d/S01cron /tmp")
        info("disable service at boot")
        j.sal.ubuntu.service_disable_start_boot("cron")
        info("Verify that file does not eixst after disabling service ")
        assert os.path.exists("/etc/rc5.d/S01cron") is False
    info("enable service at boot again to check tested method ")
    j.sal.ubuntu.service_enable_start_boot("cron")
    info("Verify cron file is exist after enabling service")
    assert os.path.exists("/etc/rc5.d/S01cron")
    if cron_file_exist:
        info("retrun back the backup file to origin path")
        j.sal.process.execute("cp /tmp/S01cron /etc/rc5.d/S01cron ")


def test026_service_uninstall():
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
    info("installing zdb from builder")
    j.builders.db.zdb.install()
    info("checking system is systemd or not ")
    mysys = _check_init_process()
    if mysys == "my_init":
        info("system is init system")
        zdb_service_file = os.path.exists("/etc/service/zdb/run")
    elif mysys == "systemd":
        info("system is init systemd")
        zdb_service_file = os.path.exists("/etc/systemd/system/zdb.service")
    else:
        info("something unexpected occurred while checking system type")
        assert mysys in ["systemd", "my_init"], "system not supported "
    if zdb_service_file is False:
        info("zdb service file config does not exist, install service so config file will created ")
        j.sal.ubuntu.service_install("zdb", j.core.tools.text_replace("{DIR_BASE}/bin"))
    info("backup the config file to /tmp before testing ")
    if mysys == "my_init":
        j.sal.process.execute("cp /etc/service/zdb/run /tmp/run_zdb")
    else:
        j.sal.process.execute("cp /etc/systemd/system/zdb.service /tmp")

    info("uninstall service to test tested method service_uninstall")
    j.sal.ubuntu.service_uninstall("zdb")
    info("Verify the zdb config file does not exist after uninstalling service ")
    if mysys == "my_init":
        assert os.path.exists("/etc/service/zdb/run") is False
    else:
        assert os.path.exists("/etc/systemd/system/zdb.service") is False
    info("return back backup file to orgin path after testing ")
    if mysys == "my_init":
        j.sal.process.execute("cp /tmp/run_zdb /etc/service/zdb/run ")
    else:
        j.sal.process.execute("cp /tmp/zdb.service /etc/systemd/system/zdb.service ")
    if zdb_service_file is False:
        info("remove service config file to return back to origin state")
        if mysys == "my_init":
            j.sal.process.execute("rm /etc/service/zdb/run")
        else:
            j.sal.process.execute("rm /etc/systemd/system/zdb.service")


def test027_whoami():
    """TC397
    check current login user

    **Test Scenario**
    #. Check whoami method output
    #. Check os current user by using command whoami
    #. Comapre step1 and step2, should be identical

    """
    info("checking whoami method output")
    sal_user = j.sal.ubuntu.whoami()
    info("checking OS whoami command output")
    rc2, os_user, err2 = j.sal.process.execute("whoami")
    info("comparing  whoami method output vs OS whoami command output")
    assert os_user.strip() == sal_user


def main():
    """
    to run:
    kosmos 'j.sal.ubuntu.test(name="ubuntu")'
    """

    before()
    test001_uptime()
    test002_service_install()
    test003_version_get()
    test004_apt_install_check()
    test005_apt_install_version()
    test006_deb_install()
    test007_pkg_list()
    test008_service_start()
    test009_service_stop()
    test010_service_restart()
    test011_service_status()
    test012_apt_find_all()
    test013_is_pkg_installed()
    test014_sshkey_generate()
    test015_apt_get_cache_keys()
    test016_apt_get_installed()
    test017_apt_install()
    test018_apt_sources_list()
    test019_apt_sources_uri_add()
    test020_apt_upgrade()
    test021_check_os()
    test022_deb_download_install()
    test023_pkg_remove()
    test024_service_disable_start_boot()
    test025_service_enable_start_boot()
    test026_service_uninstall()
    test027_whoami()

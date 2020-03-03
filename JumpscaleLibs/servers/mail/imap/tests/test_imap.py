from Jumpscale import j
from smtplib import SMTP
try:
    from imbox import Imbox
except ImportError:
    j.builders.runtimes.python3.pip_package_install("imbox", reset=True)
    from imbox import Imbox
import unittest
try:
    from imapclient import IMAPClient
except ImportError:
    j.builders.runtimes.python3.pip_package_install("imapclient", reset=True)
    from imapclient import IMAPClient
from time import sleep

skip = j.baseclasses.testtools._skip

servers = []


def after():
    info("Stop running servers")
    if servers:
        for s in servers:
            s.kill()


def info(message):
    j.tools.logger._log_info(message)


@skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/103")
def test001_imapclient_can_create_folder_in_imap():
    """
    Client can create folders in his mail.

    Steps:
    - Start imap server, should succeed.
    - List default folder, inbox should be there.
    - Create new folder, should succeed.
    """
    global servers
    servers = []

    cmd = "kosmos 'j.servers.imap.start()'"
    info("Execute {} in tmux main session".format(cmd))
    pan = j.servers.tmux.execute(cmd=cmd)
    info("Wait for 30s to make sure that the server is running")
    sleep(30)
    info("Assert that the server is running")
    assert pan.cmd_running is True, "imap server is not running"
    servers.append(pan)

    info("List default folder, inbox should be there")
    box = Imbox("0.0.0.0", "random@mail.com", "randomPW", ssl=False, port=7143)
    # assert "INBOX" in str(box.folders()[-1][0])
    # assert the whole string instead of the first element in the tuple as it is ordered alphabetically.
    assert "INBOX" in str(box.folders()[-1])

    info("Connect the client to the IMAP server")
    client = IMAPClient("0.0.0.0", port=7143, ssl=False)
    client.login("random@mail.com", "randomPW")

    box_name = j.data.idgenerator.generateXCharID(10)
    info("Create {} box".format(box_name))
    client.create_folder(box_name)

    info("Assert that the new box has been created")
    # assert box_name in str(box.folders()[-1][0])
    # assert the whole string instead of the first element in the tuple as it is ordered alphabetically.
    assert box_name in str(box.folders()[-1])

@skip("https://github.com/threefoldtech/jumpscaleX_libs/issues/62")
def test002_imapClient_get_messages_from_database():
    """
        Client can create folders in his mail.

        Steps:
        - Start smtp server, shoud success.
        - Send message to smtp server.
        - Start imap server, should succeed.
        - List default folder, inbox should be there.
        - Client should get the message from the database.
    """
    global servers
    servers = []
    cmd = "kosmos 'j.servers.smtp.start()'"
    info("Execute {} in tmux main session".format(cmd))
    pan = j.servers.tmux.execute(cmd=cmd)

    info("Wait for 30s to make sure that the server is running")
    sleep(30)
    info("Assert that the server is running")
    assert pan.cmd_running is True, "smtp server is not running"
    servers.append(pan)

    info("Connect to the server 0.0.0.0:7002")
    with SMTP("0.0.0.0", 7002) as smtp:
        body = "Hello!"
        from_mail = "test@mail.com"
        to_mail = "target@example.com"
        msg = ("From: %s\r\nTo: %s\r\n\r\n" % (from_mail, to_mail)) + body
        smtp.sendmail(from_mail, to_mail, msg)

    cmd = "kosmos 'j.servers.imap.start()'"
    info("Execute {} in tmux main session".format(cmd))
    pan_imap = j.servers.tmux.execute(cmd=cmd)
    info("Wait for 30s to make sure that the server is running")
    sleep(30)
    info("Assert that the server is running")
    assert pan_imap.cmd_running is True, "imap server is not running"
    servers.append(pan_imap)

    info("Connect to the imap server")
    box = Imbox("0.0.0.0", "random@mail.com", "randomPW", ssl=False, port=7143)

    _, last_message = box.messages()[-1]
    info("Assert that client get the message from the database")
    assert last_message.sent_from[0]["email"] == "test@mail.com"
    assert last_message.sent_to[0]["email"] == "target@example.com"
    assert last_message.body["plain"][0] == body

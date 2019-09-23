from smtplib import SMTP
from Jumpscale import j


def main(self):
    j.debug()
    try:
        db = j.data.bcdb.get("mailstest")
    except:
        print("there is no database")
    if db is not None:
        db.destroy()

    db = j.data.bcdb.new("mailstest")
    model = db.models_add("/sandbox/code/github/threefoldtech/jumpscaleX_libs/JumpscaleLibs/servers/mail/models/")

    j.servers.smtp.start()
    with SMTP("172.17.0.2", 7002) as smtp:
        # print(smtp.noop())
        # smtp.login("localhost", "password")
        # Send the mail
        msg = "Hello!"  # The /n separates the message from the headers
        smtp.sendmail("you@gmail.com", "target@example.com", msg)
    retrieved_model = db.model_get(url="jumpscale.email.message")
    data = retrieved_model.find()[-1]
    assert data.from_email == "you@gmail.com", "There is an error with the data"
    assert data.to_email == "target@example.com", "There is an error with the data"
    db.destroy()


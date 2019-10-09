from Jumpscale import j
from .gsmtpd import SMTPServer
from ..handleMail import store_message


class MailServer(SMTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.smtpInstance = j.data.bcdb.get("mails")
        self.mail_model = self.smtpInstance.model_get(url="jumpscale.email.message")

    # Do something with the gathered message
    def process_message(self, peer, mailfrom, rcpttos, data):
        self.store_mail(data)
        print("------------ Data saved In bcdb ------------")

    def store_mail(self, data, is_send=False):
        if is_send:
            return store_message(self.mail_model, data, folder="Sent")

        return store_message(self.mail_model, data)

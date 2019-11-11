from Jumpscale import j
import base64
import sendgrid
from sendgrid.helpers.mail import Email, Content, Mail, Personalization, Attachment as SendGridAttachment

Attachment = ("Attachment", ["originalfilename", "binarycontent", "type"])


class SendGridClient(j.baseclasses.object_config):
    _SCHEMATEXT = """
    @url = jumpscale.sendgrid.client
    name** = "" (S)
    apikey = ""
    """

    # def _init(self,**kwargs):
    #     self._api = None

    # @property
    # def api(self):
    #     """
    #     """
    #     if self._api is None:
    #         j.shell()
    #     return self._api

    def attachment_build(self, filepath, type="application/pdf"):
        """
        Returns a valid sendgrid attachment from typical attachment object.
        """
        data = j.sal.fs.readFile(filepath, binary=False)

        sendgridattachment = SendGridAttachment()
        sendgridattachment.content = data
        sendgridattachment.type = type
        sendgridattachment.filename = filepath
        sendgridattachment.disposition = "attachment"
        sendgridattachment.content_id = filepath

        return sendgridattachment

    def send(self, sender, subject, message, recipients=None, message_type="text/plain", attachments=None):
        """
        @param sender:string (the sender of the email)
        @param recipient:list (list of recipients of the email)
        @param subject:string (subject of the email)
        @param message:string (content of the email)
        @param message_type:string (mime type of the email content)
        @param attachments:list (list of Attachment tuple as created by self.attachment_build)
        """

        if recipients is None or recipients == []:
            return
        if attachments is None:
            attachments = []

        sg = sendgrid.SendGridAPIClient(api_key=self.apikey)
        from_email = sender
        to_email = recipients[0]
        content = Content(message_type, message)
        mail = Mail(from_email=from_email, subject=subject, to_emails=to_email, html_content=content)

        to = list(set(recipients))  # no duplicates.
        if len(to) > 1:
            for receiver in to[1:]:
                mail.personalizations[0].add_to(Email(receiver))

        for attachment in attachments:
            mail.add_attachment(self.build_attachment(attachment))

        try:
            response = sg.client.mail.send.post(request_body=mail.get())
        except Exception as e:
            self._log_info(e)
            raise e

        self._log_info("Email sent..")
        return response.status_code, response.body

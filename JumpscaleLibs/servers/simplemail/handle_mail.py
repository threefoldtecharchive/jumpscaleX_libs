from collections import namedtuple
from Jumpscale import j

import email
import email.utils
import base64

from .inbox import Inbox

inbox = Inbox()

gedis_client = j.clients.gedis.get("simplemail_handler", port=8901, package_name="threefold.simplemail")

Attachment = namedtuple(
    "Attachment", ["hashedfilename", "hashedfilepath", "hashedfileurl", "originalfilename", "binarycontent", "type"]
)

ATTACHMENTS_PATH = "/sandbox/mail_attachments/"


def _parse_email_body(body):
    """
    Parses email body and searches for the attachements
    :return: dict of (body, attachments, to_mail, from_mail, subject, html_body, headers, date)
    :rtype: dict
    """

    message = email.message_from_string(body)
    return _parse_email(message)


def _parse_email(message):
    to_mail = message.get("To")
    from_mail = message.get("From")
    subject = message.get("Subject") if message.get("Subject") is not None else ""
    headers = _get_headers(message.items())
    # Get the date from the headers
    val = [item["value"] for item in headers if item["key"].lower() == "date"]
    date = val[0] if len(val) != 0 else ""
    body = ""
    html_body = ""
    attachments = []
    g = message.walk()
    if message.is_multipart():
        next(g)  # SKIP THE ROOT ONE.

    for part in g:
        part_content_type = part.get_content_type()
        part_body = part.get_payload()
        part_filename = part.get_param("filename", None, "content-disposition")

        # get the body of the mail
        if part_content_type == "text/plain" and part_filename is None:
            body += part_body

        elif part_content_type == "text/html" and part_filename is None:
            html_body += part_body

        elif part_content_type is not None and part_filename is not None:
            attachments.append({"name": part_filename, "content": part_body, "contentType": part_content_type})

    return {
        "body": body,
        "attachments": attachments,
        "to": to_mail,
        "from": from_mail,
        "subject": subject,
        "htmlbody": html_body,
        "headers": headers,
        "date": date,
    }


def _get_headers(headers):
    rest_headers = []
    reserved_headers = ["To", "From", "Subject"]
    for key, val in headers:
        if key not in reserved_headers:
            rest_headers.append({"key": key, "value": val})
    return rest_headers


def _handle_attachments(subject, attachments):
    # create a dir for each mail to be easy to access
    attachments_fs_paths = []
    path = j.sal.fs.joinPaths(ATTACHMENTS_PATH, subject)
    j.sal.fs.createDir(path)

    for attachment in attachments:
        attachment_name = attachment["name"]
        attachment_content = attachment["content"]

        # make sure attachments path exists
        current_datatime = j.data.time.formatTime(j.data.time.epoch, formatstr="%Y-%m-%d_%H-%M-%S")
        file_path = f"{path}/{current_datatime}_{attachment_name}"
        attachments_fs_paths.append(file_path)
        file_content = base64.decodebytes(attachment_content.encode())
        j.sal.fs.writeFile(file_path, file_content)

    return attachments_fs_paths


@inbox.collate
def handle(to, sender, subject, body):
    print(f"\n**Receiving**\n\n{to}\n{sender}\n{subject}\n{body}")

    email_body = _parse_email_body(body)

    # get attachments and save them in file system in ATTACHMENTS_PATH
    attachments = email_body.get("attachments", None)

    attachments_fs_paths = _handle_attachments(subject, attachments)
    email_from = email_body.get("from")
    email_to = email_body.get("to")
    subject = email_body.get("subject")
    body = email_body.get("body")
    htmlbody = email_body.get("htmlbody")
    date = j.data.time.formatTime(j.data.time.epoch, formatstr="%Y-%m-%d_%H-%M-%S")

    # save the mail using gedis client
    gedis_client.actors.simplemail.save_mail(
        email_from=email_from,
        email_to=email_to,
        subject=subject,
        body=body,
        attachments=attachments_fs_paths,
        htmlbody=htmlbody,
        date=date,
    )


def serve_forever(host, port):
    """
    Start mail services.
    :param host: Host
    :param port: Port
    """
    print("Starting mail-in/out on {}:{}".format(host, port))
    inbox.serve(address=host, port=port)

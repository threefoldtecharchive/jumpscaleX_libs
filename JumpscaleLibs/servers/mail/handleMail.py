import email
from collections import namedtuple
import email.utils
from pyblake2 import blake2b

Attachment = namedtuple(
    "Attachment", ["hashedfilename", "hashedfilepath", "hashedfileurl", "originalfilename", "binarycontent", "type"]
)


def parse_email_body(body):
    """
    Parses email body and searches for the attachements
    :return: (body, attachments)
    :rtype: tuple
    """

    message = email.message_from_string(body)

    to_mail = message.get("To")
    from_mail = message.get("From")
    subject = message.get("Subject") if message.get("Subject") is not None else ""
    headers = get_headers(message.items())
    body = b""
    html_body = b""
    attachments = []
    g = message.walk()
    if message.is_multipart():
        next(g)  # SKIP THE ROOT ONE.

    for part in g:
        part_content_type = part.get_content_type()
        part_body = part.get_payload(decode=True)

        part_filename = part.get_param("filename", None, "content-disposition")

        # get the body of the mail
        if part_content_type == "text/plain" and part_filename is None:
            body += part_body

        elif part_content_type == "text/html" and part_filename is None:
            html_body += part_body

        elif part_content_type is not None and part_filename is not None:
            attachments.append({"name": part_filename, "content": part_body, "contentType": part_content_type})

    bhash = blake2b()
    allData = body + html_body
    bhash.update(allData)
    hashed_data = bhash.hexdigest()
    return {
        "name": hashed_data,
        "body": body.decode("ascii"),
        "attachments": attachments,
        "to": to_mail,
        "from": from_mail,
        "subject": subject,
        "htmlbody": html_body.decode("ascii"),
        "headers": headers,
    }


def get_headers(headers):
    rest_headers = []
    reserved_headers = ["To", "From", "Subject"]
    for key, val in headers:
        if key not in reserved_headers:
            rest_headers.append({"key": key, "value": val})
    return rest_headers


if __name__ == "__main__":
    data = 'To: rafy@gmail.com\nFrom: Rafy <rafy@incubaid.com>\nSubject: testing subject\nMessage-ID: <ace3555b-1715-3177-d707-ad8a982f0aeb@incubaid.com>\nDate: Thu, 19 Sep 2019 12:29:06 +0200\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101\n Thunderbird/60.8.0\nMIME-Version: 1.0\nContent-Type: multipart/mixed;\n boundary="------------54B39785043A597FAEBBBA3E"\nContent-Language: en-US\n\nThis is a multi-part message in MIME format.\n--------------54B39785043A597FAEBBBA3E\nContent-Type: multipart/alternative;\n boundary="------------7235A5D86007E410F6A6660D"\n\n\n--------------7235A5D86007E410F6A6660D\nContent-Type: text/plain; charset=utf-8; format=flowed\nContent-Transfer-Encoding: 7bit\n\ntesting body\n\n\n  Testing html\n\n\n\n--------------7235A5D86007E410F6A6660D\nContent-Type: text/html; charset=utf-8\nContent-Transfer-Encoding: 7bit\n\n<html>\n  <head>\n\n    <meta http-equiv="content-type" content="text/html; charset=UTF-8">\n  </head>\n  <body text="#000000" bgcolor="#FFFFFF">\n    <p>testing body <br>\n    </p>\n    <h1>Testing html </h1>\n    <p><br>\n    </p>\n  </body>\n</html>\n\n--------------7235A5D86007E410F6A6660D--\n\n--------------54B39785043A597FAEBBBA3E\nContent-Type: text/plain; charset=UTF-8;\n name="how to scedule a job"\nContent-Transfer-Encoding: base64\nContent-Disposition: attachment;\n filename="how to scedule a job"\n\nZnJvbSBKdW1wc2NhbGUuc2VydmVycy5teWpvYnMuTXlKb2JzRmFjdG9yeSBpbXBvcnQgYWRk\nCmouc2VydmVycy5teWpvYnMud29ya2VycwpqLnNlcnZlcnMubXlqb2JzLnNjaGVkdWxlKGFk\nZCw1NDU0NTMpCgo=\n--------------54B39785043A597FAEBBBA3E--'
    data = "To: testing@dd.com\nFrom: Rafy <rafy@incubaid.com>\nSubject: trial 2\nMessage-ID: <34cefd88-2af6-906d-0ce1-889ba50ea117@incubaid.com>\nDate: Sun, 22 Sep 2019 16:23:31 +0200\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101\n Thunderbird/60.8.0\nMIME-Version: 1.0\nContent-Type: text/plain; charset=utf-8; format=flowed\nContent-Transfer-Encoding: 7bit\nContent-Language: en-US\n\ntesting the second trial\n"
    result = parse_email_body(data)
    print("done")

# https://github.com/incubaid/crm/blob/master/crm/mailer.py

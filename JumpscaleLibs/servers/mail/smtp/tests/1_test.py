from smtplib import SMTP


def main(self):
    with SMTP("localhost", 7002) as smtp:
        print(smtp.noop())
        smtp.login("localhost", "password")
        # Send the mail
        msg = "Hello!"  # The /n separates the message from the headers
        smtp.sendmail("you@gmail.com", "target@example.com", msg)

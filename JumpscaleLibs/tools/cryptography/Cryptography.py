from Jumpscale import j
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class Cryptography(j.baseclasses.object):
    __jslocation__ = "j.tools.cryptography"

    def _init(self, **kwargs):
        pass

    def generated_key(self, password , msg_salt):
        password_provided = password  # This is input in the form of a string
        password = password_provided.encode()  # Convert to type bytes
        salt = msg_salt.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))  # Can only use kdf once
        return  key


    def encrypt_msg(self, key, msg):
        message = msg.encode()
        f = Fernet(key)
        encrypted = f.encrypt(message)
        return encrypted.decode()


    def decrypt_msg(self, key, msg_encrypted):
        msg_encrypted = msg_encrypted.encode()
        f = Fernet(key)
        decrypted = f.decrypt(msg_encrypted)
        return decrypted.decode()


    def encrypt_file(self, key, path, out_path ):

        with open(path, 'rb') as f:
            data = f.read()

        fernet = Fernet(key)
        encrypted = fernet.encrypt(data)

        with open(out_path, 'wb') as f:
            f.write(encrypted)
        return out_path


    def decrypt_file(self, key, path, out_path):
        with open(path, 'rb') as f:
            data = f.read()

        fernet = Fernet(key)
        decrypt = fernet.decrypt(data)

        with open(out_path, 'wb') as f:
            f.write(decrypt)
        return  out_path
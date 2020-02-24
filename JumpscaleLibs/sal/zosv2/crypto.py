from nacl import public
from nacl.signing import VerifyKey, SigningKey
from nacl.encoding import Base64Encoder
from nacl.public import SealedBox


def encrypt_for_node(public_key, payload):
    """
    encrypt payload with the public key of a node
    so only the node itself can decrypt it
    
    use this if you have sensitive data to send in a reservation
    
    :param public_key: public key of the node, hex-encoded.
    :type public_key: str
    :param payload: any data you want to encrypt
    :type payload: bytes
    :return: encrypted data. you can use this safely into your reservation data
    :rtype: str
    """
    node_public_bin = j.data.hash.hex2bin(public_key)
    node_public = VerifyKey(node_public_bin)
    box = SealedBox(node_public.to_curve25519_public_key())

    encrypted = box.encrypt(payload)
    return j.data.hash.bin2hex(encrypted)

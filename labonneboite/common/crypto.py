# From https://nitratine.net/blog/post/encryption-and-decryption-in-python/
from labonneboite.conf import settings
from cryptography.fernet import Fernet


def encrypt(message_as_string):
    message_as_bytes = message_as_string.encode()
    f = Fernet(settings.CRYPTOGRAPHY_SECRET_KEY)
    encrypted_message_as_bytes = f.encrypt(message_as_bytes)
    encrypted_message_as_string = encrypted_message_as_bytes.decode()
    return encrypted_message_as_string


def decrypt(encrypted_message_as_string):
    encrypted_message_as_bytes = encrypted_message_as_string.encode()
    f = Fernet(settings.CRYPTOGRAPHY_SECRET_KEY)
    message_as_bytes = f.decrypt(encrypted_message_as_bytes)
    message_as_string = message_as_bytes.decode()
    return message_as_string

import os
import bcrypt
from encryption.encryption_utils import EncryptionUtils as utils
from Crypto.Hash import SHA3_256
import logging

logging.basicConfig(level=logging.INFO)


class EncryptionContext:

    def __init__(self, is_new_user: bool,
                 user_passphrase: str,
                 username: str,
                 user_public_key: str = None):
        sha3_256 = SHA3_256.new()
        self.__user_passphrase = sha3_256.update(user_passphrase.encode('utf-8')).hexdigest()
        self.__username = username
        self.__public_key = user_public_key
        if is_new_user:
            self._init_user_context()
        else:
            self._load_user_context()

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def check_password(password, hashed_password) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @property
    def public_key(self) -> str:
        return self.__public_key

    @property
    def username(self) -> str:
        return self.__username

    def _init_user_context(self):
        public_key, private_key = utils.generate_public_private_keys(self.__user_passphrase)
        self.__public_key = public_key
        self.__private_key = private_key
        path = os.path.dirname(__file__)
        with open(f"{path}/keys/{self.username}_pk.key", "wb") as f:
            f.write(private_key)
        logging.info(f"created new user context for {self.username}")

    def _load_user_context(self):
        assert self.public_key is not None
        path = os.path.dirname(__file__)
        with open(f"{path}/keys/{self.username}_pk.key", "rb") as f:
            self.__private_key = f.read()
        logging.info(f"loaded user context for {self.username}")

    def encrypt_message(self, message: bytes, recipient_public_key: bytes) -> tuple[tuple[bytes, bytes], bytes]:
        session_key = utils.generate_session_key()
        cipher_text = utils.encrypt_message_with_session_key(message, session_key)
        enc_session_key = utils.encrypt_session_key_with_public_key(session_key, recipient_public_key)
        return cipher_text, enc_session_key

    def decrypt_message(self, cipher_text: bytes, cipher_nonce: bytes, enc_session_key: bytes) -> bytes:
        session_key = utils.decrypt_session_key_with_private_key(enc_session_key,
                                                                 self.__private_key,
                                                                 self.__user_passphrase)
        plain_text = utils.decrypt_message_with_session_key(cipher_text, session_key, cipher_nonce)
        return plain_text


if __name__ == '__main__':
    context = EncryptionContext(True, "password", "test")
    public_key = context.public_key
    context2 = EncryptionContext(False, "password", "test", public_key)
    print(f"public key: {context2.public_key}")
    print(f"username: {context2.username}")

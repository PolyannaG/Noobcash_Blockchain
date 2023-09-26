import binascii
from Crypto.PublicKey import RSA


class wallet:
    def __init__(self):
        private_key = RSA.generate(2048)
        self.private_key = private_key.exportKey(
            format="PEM"
        )  # export private key from key object, text encoding
        self.public_key = private_key.publickey().exportKey(
            format="PEM"
        )  # get public key object that is the pair of the private and export public key from object
        sender_address = binascii.b2a_hex(self.public_key).decode("utf-8")
        self.address = sender_address  # the address of the user is the public key

    def balance(
        self, NBCs_list
    ):  # parameter is list of unsent UTXOs, returns total NBCs
        total = 0
        for item in NBCs_list:  # sum all the UTXOs of the node
            total += item[3]
        return total

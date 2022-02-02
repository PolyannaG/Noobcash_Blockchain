import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4



class wallet:

	def __init__(self):
		##set

		#self.public_key
		#self.private_key
		#self_address
		#self.transactions
		private_key=RSA.generate(2048)
		self.private_key=private_key.exportKey(format='PEM')               # export private key from key object, text encoding
		self.public_key=private_key.publickey().exportKey(format='PEM')    # get public key object that is the pair of the private and export public key from object
		self.address=self.public_key                   					   # the address of the user is the public key
		self.transactions=[]						                       # no transactions yet						


	def balance():
		return

#wall=wallet()
#print(binascii.b2a_hex(wall.public_key).decode('utf-8'))
#print(binascii.b2a_hex(wall.public_key).decode('ascii'))
#print(binascii.b2a_hex(wall.private_key))

import binascii
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import time
import random


class Transaction:

    def __init__(self, sender_address, sender_private_key, recipient_address, value):

        self.sender_address=sender_address                  # the sender wallet's public key
        self.receiver_address=recipient_address             # the receiver wallet's public key
        self.amount=value                                   # the amount to be transfered
        self.sender_private_key=sender_private_key          # the sender wallet's private key        
        
        N=random.randint(10,20)                                                                                    # random int
        rand_string=Crypto.Random.get_random_bytes(N)                                                              # random byte string of length N
        message_to_hash=str(sender_address)+str(recipient_address)+str(value)+str(rand_string)+str(time.time())    # transaction hash will be created from this message
        self.transaction_id=SHA.new(message_to_hash.encode()).hexdigest()                                           # encode() converts the string into bytes to be acceptable by hash function
                                                                                                                   # create hash object and get encoded hash in hexadecimal format                  
        self.inputs=[]                                       # input list initially empty, will be updated by create_transaction() 
        self.outputs=[]                                      # output list initially empty, will be updated by create_transaction() 


    def to_dict(self,add_signature=False):                   # function to convert transaction from object to dictionary
        # convert addressed from bytes to sendabe form
        if (type(self.sender_address)==bytes):
                sender_address=binascii.b2a_hex(self.sender_address).decode('utf-8')
        else: 
            sender_address=self.sender_address
        if (type(self.receiver_address)==bytes):
            receiver_address=binascii.b2a_hex(self.receiver_address).decode('utf-8')
        else: 
            receiver_address=self.receiver_address

        if not add_signature:                                                 # do not add transaction signature (used for calculating signature)
            transaction_dict=({'sender_address' : sender_address, 
                                'receiver_address' : receiver_address,
                                'amount' : self.amount,
                                'transaction_id' : str(self.transaction_id),
                                'transaction_inputs' : self.inputs,
                                'transaction_outputs' : self.outputs})
                                
        else:                                                                # add transaction signature (used  for sending transaction)
            transaction_dict=({'sender_address' : sender_address, 
                            'receiver_address' : receiver_address,
                            'amount' : self.amount,
                            'transaction_id' : str(self.transaction_id),
                            'transaction_inputs' : self.inputs,
                            'transaction_outputs' : self.outputs,
                            'signature': self.signature})
        return transaction_dict

    def sign_transaction(self):                                              # function to calculate transaction signature
        key = RSA.importKey(self.sender_private_key)                         # import RSA key
        transaction_to_sign=str(self.to_dict())                              # convert transaction to dictionary --> get all its fields
        hashed_transaction=SHA.new(transaction_to_sign.encode('utf-8'))      # hash message (transaction)
        signature=PKCS1_v1_5.new(key).sign(hashed_transaction)               # sign using private key
        self.signature=binascii.b2a_hex(signature).decode('utf-8')           # save signature in utf-8 form
   
       
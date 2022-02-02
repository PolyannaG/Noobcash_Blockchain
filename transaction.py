from collections import OrderedDict

import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import requests
from flask import Flask, jsonify, request, render_template
import time
import random
from base64 import b64decode
#from wallet import wallet          # will be removed, testing only


class Transaction:

    def __init__(self, sender_address, sender_private_key, recipient_address, value):


        ##set

        #self.sender_address: To public key του wallet από το οποίο προέρχονται τα χρήματα
        #self.receiver_address: To public key του wallet στο οποίο θα καταλήξουν τα χρήματα
        #self.amount: το ποσό που θα μεταφερθεί
        #self.transaction_id: το hash του transaction
        #self.transaction_inputs: λίστα από Transaction Input 
        #self.transaction_outputs: λίστα από Transaction Output 
        #selfSignature
        self.sender_address=sender_address
        self.receiver_address=recipient_address
        self.amount=value
        self.sender_private_key=sender_private_key
        
        N=random.randint(10,20)                                                                                    # random int
        rand_string=Crypto.Random.get_random_bytes(N)                                                              # random byte string of length N
        message_to_hash=str(sender_address)+str(recipient_address)+str(value)+str(rand_string)+str(time.time())    # transaction hash will be created from this message
        self.transacton_id=SHA.new(message_to_hash.encode()).hexdigest()                                           # encode() converts the string into bytes to be acceptable by hash function
                                                                                                                   # create hash object and get encoded hash in hexadecimal format                  
        self.transaction_inputs=[]    # input list initially empty, will be updated by create_transaction() 
        self.transaction_outputs=[]   # output list initially empty, will be updated by create_transaction() ?

    


    def to_dict(self):       
        """
        Convert transaction info to dictionary
        """
        transaction_dict=({'sender_address' : self.sender_address, 
                            'receiver_address' : self.receiver_address,
                            'amount' : self.amount,
                            'transaction_id' : self.transacton_id,
                            'transaction_inputs' : self.transaction_inputs,
                            'transaction_outputs' : self.transaction_outputs})
        return transaction_dict

    def sign_transaction(self):
        """
        Sign transaction with private key
        """
        
        key = RSA.importKey(self.sender_private_key)                         # import RSA key
        transaction_to_sign=str(self.to_dict())                              # convert transaction to dictionary --> get all its fields
        hashed_transaction=SHA.new(transaction_to_sign.encode('utf-8'))      # hash message (transaction)
        signature=PKCS1_v1_5.new(key).sign(hashed_transaction)               # sign using private key
        self.signature=binascii.b2a_hex(signature).decode('utf-8')           # save signature in utf-8 form
   
       

#wall=wallet()      
#tran=Transaction("ddd",wall.private_key,"www",10)
#tran.sign_transaction()
from ast import excepthandler
from block import Block
from wallet import wallet
from transaction import Transaction

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

class Node:
	def __init__(self):
		#self.NBC=100;
		##set

		#self.chain
		self.current_id_count=0
		#self.NBCs
		self.id=None	# node id in ring
		self.NBCs=[]    # list to hold unspent UTXOs of all nodes --> should it keep total amount of unspent UTXOs or different transaction outputs?
						# https://academy.binance.com/en/glossary/unspent-transaction-output-utxo
		#self.wallet
		self.wallet=self.create_wallet()  # wallet will be created by create_wallet() --> should we call it here??

		#slef.ring[]   #here we store information for every node, as its id, its address (ip:port) its public key and its balance 
		self.ring=[]
		print("creating new node instance")



	def create_new_block(self,index,previousHash,nonce):
		print("creating new block")
		new_block=Block(index,previousHash,nonce)
		return new_block

	def create_wallet(self):
		#create a wallet for this node, with a public key and a private key
		return wallet()
		

	def register_node_to_ring(self,public_key,address):
		#add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
		#bottstrap node informs all other nodes and gives the request node an id and 100 NBCs
		try: 
			node_info=[{'node_id': self.current_id_count+1, 'address': address, 'public_key': public_key, 'balance': 0}]  # 100 NBC to be given later with transaction???
			self.current_id_count+=1
			self.ring.append(node_info)

			# logic missing!!!! -> give money through transaction, if we have n nodes, broadcast
			return True
		except:
			return False


	def create_transaction(self,sender, receiver,amount, signature=None):
		#remember to broadcast it
		
		#logic missing! inputs, outputs, broadcast etx, only for testing
		new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)
		new_transaction.sign_transaction()
		return new_transaction


	def broadcast_transaction():
		return



	def validdate_transaction(transaction):                          # in what form will the transaction be received here? if it is received as dictionary, we have to make changes
		#use of signature and NBCs balance
		key=RSA.importKey(transaction.sender_address)                # public key of sender is the sender's address
		hashed_transaction=SHA.new(transaction.encode('utf-8'))      # hash transaction to verify its signature
		try:
			is_verified=PKCS1_v1_5.new(key).verify(hashed_transaction,transaction.signature)  # verify transaction signature
			if is_verified:                                          # transaction signature validated
				return                                               # here we will check UTXOs
		except:
			return False

        


	def add_transaction_to_block():
		#if enough transactions  mine
		return



	def mine_block():
		return


	def broadcast_block():
		return

		

	#def valid_proof(.., difficulty=MINING_DIFFICULTY):




	#concencus functions

	def valid_chain(self, chain):
		#check for the longer chain accroose all nodes
		return

	def resolve_conflicts(self):
		#resolve correct chain
		return



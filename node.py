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
						# dictionary: NBCs(i) will be a set that holds transaction outputs (transactions from which the
						# node has received money): list of tuples where first item is the transaction id and the second item is the amount the node gained
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
			node_info={'node_id': self.current_id_count+1, 'address': address, 'public_key': public_key, 'balance': 0}  # 100 NBC to be given later with transaction???
			self.current_id_count+=1
			self.ring.append(node_info)

			# logic missing!!!! -> give money through transaction, if we have n nodes, broadcast
			return True
		except:
			return False


	def create_transaction(self,sender, receiver,amount, signature=None):
		#remember to broadcast it
		
		#logic missing! inputs, outputs, broadcast etx, only for testing
		if (sender=='0'):																			  # transaction for genesis block	
			new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)
			new_transaction.transaction_inputs=[]
			new_transaction.transaction_outputs=[(receiver,amount)]
			new_transaction.sign_transaction()
		else:                           															  # usual case
			for node_item in self.ring:																  # check that node is indeed part of the ring
				if (node_item['address']==sender):
					sender_id=node_item['node_id']
			if sender_id==None:						
				return "Sender not part of ring." ,400
			elif sender_id!=self.id:																  # check that the node is indeed the current one (for safety, should always be true)
				return "Sender not current node, you do not own this wallet.", 400
			else:
				total=self.wallet.balance(self.NBCs(sender_id))										  # check that the node has enough NBCs for the transaction	
				if (total<amount):
					return "Not enough NBCs for the spesified transaction.", 400
				else:                                                                                 # all checks complete, we are ready to start the transaction
					try:
						inputs=[]
						outputs=[]																		
						cur_sum=0
						for item in self.NBCs(sender_id):											  # find the previous transactions the money will come from
							cur_sum+=item[1]
							inputs.append(item)
							if cur_sum>=amount:
								break
						difference=cur_sum-amount													  # calculate how much money the sender has to get back				
						if (difference!=0):
							outputs.append((sender,difference))
						outputs.append((receiver,amount))                                             # the money to be given to receiver
						new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)   # create the trascaction
						new_transaction.transaction_inputs=inputs                                     # add the trasaction inputs
						new_transaction.transaction_outputs=outputs          		              	  # add the transaction outputs		
						new_transaction.sign_transaction()											  # sign transaction		
						self.broadcast_transaction(new_transaction)                                   # broadcast to all nodes, should it be called by new thread??
						return "Transaction created successfully", 200
					except:                                                                           # Case of unexpected error
						return "Error creating transaction.", 500


		return new_transaction


	def broadcast_transaction(self,transaction):
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



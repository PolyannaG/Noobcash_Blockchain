from ast import excepthandler
from binascii import a2b_hex
import binascii
from inspect import signature
from platform import node
from block import Block
from wallet import wallet
from transaction import Transaction
import requests
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import time
import itertools

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
		
		self.id=None	# node id in ring
		self.NBCs={}    # dictionary to hold unspent UTXOs of all nodes --> should it keep total amount of unspent UTXOs or different transaction outputs?
						# https://academy.binance.com/en/glossary/unspent-transaction-output-utxo
						# dictionary: NBCs(i) will be a set that holds transaction outputs (transactions from which the
						# node has received money): list of tuples where first item is the transaction id and the second item is the amount the node gained
		
		self.wallet=self.create_wallet()  # wallet will be created by create_wallet() --> should we call it here??  
		self.ring=[]    #here we store information for every node, as its id, its address (ip:port) its public key and its balance 
		print("creating new node instance")



	def create_new_block(self,index,previousHash,nonce):
		print("creating new block")
		new_block=Block(index,previousHash,nonce)
		return new_block

	def create_wallet(self):
		#create a wallet for this node, with a public key and a private key
		return wallet()
		

	def register_node_to_ring(self,public_key,address, contact):
		#add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
		#bottstrap node informs all other nodes and gives the request node an id and 100 NBCs
		try: 
			node_info={'node_id': self.current_id_count+1,'contact':contact, 'address': address, 'public_key': public_key, 'balance': 0}  # 100 NBC to be given later with transaction???
			self.current_id_count+=1
			self.ring.append(node_info)

			# logic missing!!!! -> give money through transaction, if we have n nodes, broadcast
			return True
		except:
			return False


	def create_transaction(self,sender, receiver,amount, signature=None):
		#remember to broadcast it
		
		#logic missing!  broadcast !!!!
		if (sender=='0'):																			  # transaction for genesis block	
			new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)
			new_transaction.transaction_inputs=[]
			new_transaction.transaction_outputs=[(receiver,amount)]
			new_transaction.sign_transaction()
			
			return 'Transaction created succesfully', 200, new_transaction
		
		else:   
			print('creating transaction')                        									  # usual case
			
			for node_item in self.ring:																  # check that node is indeed part of the ring
				if (node_item['address']==sender):
					sender_id=node_item['node_id']
			if sender_id==None:						
				return "Sender not part of ring." ,400, None
			elif sender_id!=self.id:																  # check that the node is indeed the current one (for safety, should always be true)
				return "Sender not current node, you do not own this wallet.", 400, None
			else:
				total=self.wallet.balance(self.NBCs[sender_id])										  # check that the node has enough NBCs for the transaction	
				if (total<amount):
					return "Not enough NBCs for the spesified transaction.", 400, None
				else:                                                                                 # all checks complete, we are ready to start the transaction
					try:

						inputs=[]
						outputs=[]																		
						cur_sum=0
						
						for item in self.NBCs[sender_id]:											  # find the previous transactions the money will come from
							cur_sum+=item[1]
							inputs.append(item)
							if cur_sum>=amount:
								break
						
						difference=cur_sum-amount													  # calculate how much money the sender has to get back				
						if (difference!=0):
							outputs.append((sender,difference))
						outputs.append((receiver,amount))                                             # the money to be given to receiver
						
						new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)   # create the trascaction
						new_transaction.inputs=inputs                                                 # add the trasaction inputs
						new_transaction.outputs=outputs          		              	              # add the transaction outputs	
						new_transaction.sign_transaction()											  # sign transaction	
						
						#threading.Thread(target=self.broadcast_transaction, args=(new_transaction,)).start()	 # broadcast to all nodes, should it be called by new thread??
						threading.Thread(target=asyncio.run,args=(self.broadcast_transaction(new_transaction),)).start()
						#broadcast_thread.start()    
						                           
						return "Transaction created successfully", 200 , new_transaction
					except:                                                                           # Case of unexpected error
						return "Error creating transaction.", 500, None


	def persistent_sending(*args):
		_,node_,trans_to_broadcast=args
		sent=False
		while(not sent):
			try:
				res=requests.post('{}/transactions/receive'.format(node_['contact']), json=trans_to_broadcast)
				if (res.status_code==200):                                     # transaction sent
					print('transaction sent to node:', node_['node_id'])			
					sent=True			
				else:                                                          # error in sending
					print("error sending transaction to node:", node_['node_id'], res.json()['message'])
					sent=False
					sent=True
			except:
				print("error sending transaction to node:", node_['node_id'])
				sent=False
				sent=True



	async def broadcast_transaction(self,transaction):
		trans_to_broadcast=transaction.to_dict(True)
		#print(trans_to_broadcast)
		for node_ in self.ring:
			sent_thread=threading.Thread(target=self.persistent_sending,args=(node_,trans_to_broadcast))
			sent_thread.start()

			
						


	def validate_transaction(self,transaction):                       # in what form will the transaction be received here? if it is received as dictionary, we have to make changes
		#use of signature and NBCs balance
		print('validating')		
		sender_address=a2b_hex(transaction.sender_address)
		key=RSA.importKey(sender_address)                              # public key of sender is the sender's address
		print('key imported')
		signature=a2b_hex(transaction.signature)	
		trans_to_hash=str(transaction.to_dict())
		hashed_transaction=SHA.new(trans_to_hash.encode('utf-8'))      # hash transaction to verify its signature
		
		try:	
			
			# signature verification
			# signature=a2b_hex(transaction.signature)
			# print('signature')
			is_verified=PKCS1_v1_5.new(key).verify(hashed_transaction,signature)  # verify transaction signature			

			if is_verified:                                          # transaction signature validated, now we check UTXOs
				print('verified singature')
			# check that transaction inputs are unspent
				for item in self.ring:
					if transaction.sender_address==item['address']:
						sender_id=item['node_id']
						print('found sender in ring',sender_id)
				for input in transaction.inputs:                     # check that every input is unspent
					found_utxo=False
					print(self.NBCs)

					for utxo in self.NBCs[sender_id]:           
						if utxo[0]==input[0]:
							found_utxo=True
							self.NBCs[sender_id].remove(utxo)
					if not found_utxo:
						print('utxo not unspent')
						return False
				
			# add transaction outputs to UTXOs list (NBCs)
				
				for output in transaction.outputs:                 # inputs unspent, time to add outputs to NBCs list
					for item in self.ring:                         # find id of node whose wallter will get the NBCs
						if output[0]==item['address']:
							print('found node id',item['node_id'])
							node_id=item['node_id']
					if node_id==None:
						print('Node id not found in ring')
						return False
					self.NBCs[node_id].append((transaction.transaction_id,output[1]))
					print('new nbcs:', self.NBCs)
			
			return True                                         
		except:
			return False



	def persistent_sending_data_to_nodes(self,*args):
		node_,data,num=args
		sent=False
		while(not sent):																# try to send ring until succesful
			try:
				res=requests.post('{}/ring/get'.format(node_['contact']), json=data)
				if (res.status_code==200):                                              # ring sent
					print('ring sent to node:', node_['node_id'])			
					sent=True	
					num[0]+=1															# increase number of nodes that have received the ring
					if (num[0]==len(self.ring)):                                        # if all nodes have received the ring, time to broadcast blockchain
						# LOGIC MISSING!!!!!!!!!!! BLOCKCHAIN BROADCAST!!!!
						self.make_transfer()											# after having broadcasted the blockchain it is time to make the first transactions
						
				else:                                                                   # error in sending
					print("error sending ring to node:", node_['node_id'], res.json()['message'])
					sent=False
					
			except:
				print("error2 sending ring to node:", node_['node_id'])
				sent=False
				
				

	def send_data_to_nodes_give_blockchain_and_make_transfer(self):                                      
		# function for the bootstrap to send to the nodes the ring, the blockchain so far, and to create and send the initial transactions
		data={"ring": self.ring}       # data to send at first is the ring
		num=[0]						   # variable to hold how many nodes have received the ring
		for node_ in self.ring:        # send ring to all nodes in ring
			t=threading.Thread(target=self.persistent_sending_data_to_nodes, args=(node_,data,num))     # new thread for each node, call insinde function for the rest of the functionality
			t.start()
			
	
	def make_transfer(self):                   # function to transfer 100 NBCs from the bootstrap node to all the other nodes of the ring
		for node_ in self.ring:                # for every node in the ring:
			if node_['node_id']==0:            # except from bootstrap
				print('not for bootstrap')
				continue
			message,error_code,trans=self.create_transaction(self.wallet.address,node_['address'],100)
			if error_code!=200:
				return message,error_code,False
			print('finished',node_['node_id'])
			


       


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



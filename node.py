from ast import excepthandler
from binascii import a2b_hex
import binascii
from msvcrt import locking
import random
from dotenv import load_dotenv
from block import Block
from wallet import wallet
from transaction import Transaction
import requests
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import time
import os
import uuid
import copy
import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

class Node:
	def __init__(self):
		#self.NBC=100;
		##set

		NBCs_lock=threading.Lock()
		valid_transactions_lock=threading.Lock()
		cur_block_lock=threading.Lock()
		chain_lock=threading.Lock()
		self.locks={'NBCs': NBCs_lock,'valid_trans': valid_transactions_lock,'cur_block': cur_block_lock,'chain': chain_lock}

		self.valid_transaction_ids=set()

		self.block_capacity=2

		self.chain=[]
		self.current_id_count=0
		self.node_number=None
		
		self.id=None	# node id in ring
		self.NBCs={}    # dictionary to hold unspent UTXOs of all nodes --> should it keep total amount of unspent UTXOs or different transaction outputs?
						# https://academy.binance.com/en/glossary/unspent-transaction-output-utxo
						# dictionary: NBCs(i) will be a set that holds transaction outputs (transactions from which the
						# node has received money): list of tuples where first item is the transaction id and the second item is the amount the node gained
		
		self.wallet=self.create_wallet()  # wallet will be created by create_wallet() --> should we call it here??  
		self.ring=[]    #here we store information for every node, as its id, its address (ip:port) its public key and its balance
		self.current_block=None 
		print("creating new node instance")



	def create_new_block(self,index,previousHash,nonce,capacity=5):
		print("creating new block")
		new_block=Block(index,previousHash,nonce,capacity)
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
		if (sender=='0'):
			#print('hereeeeeeee')	
			print(amount)																		  # transaction for genesis block	
			new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)
			new_transaction.transaction_inputs=[]
			#new_transaction.transaction_outputs=[(receiver,amount)]
			new_transaction.outputs=[(str(uuid.uuid1()),new_transaction.transaction_id,binascii.b2a_hex(receiver).decode('utf-8'),amount)]
			new_transaction.sign_transaction()
			
			return 'Transaction created succesfully', 200, new_transaction
		
		else:   
			print('creating transaction')                        									  # usual case
			
			for node_item in self.ring:																  # check that node is indeed part of the ring
				if (node_item['address']==sender):
					sender_id=node_item['node_id']
			print(sender_id)
			if sender_id==None:						
				return "Sender not part of ring." ,400, None
			elif sender_id!=self.id:																  # check that the node is indeed the current one (for safety, should always be true)
				return "Sender not current node, you do not own this wallet.", 400, None
			else:
				self.locks['NBCs'].acquire()
				total=self.wallet.balance(self.NBCs[sender_id])	
				print(self.NBCs)									  # check that the node has enough NBCs for the transaction	
				if (total<amount):
					return "Not enough NBCs for the spesified transaction.", 400, None
				else:                                                                                 # all checks complete, we are ready to start the transaction
					try:
						print('heloooo')

						inputs=[]
						outputs=[]																		
						cur_sum=0
						
						for item in self.NBCs[sender_id]:											  # find the previous transactions the money will come from
							cur_sum+=item[3]
							inputs.append(item)
							if cur_sum>=amount:
								break
						self.locks['NBCs'].release()
						difference=cur_sum-amount													  # calculate how much money the sender has to get back				
						new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)   # create the trascaction
						if (difference!=0):
							outputs.append((str(uuid.uuid1()),new_transaction.transaction_id,sender,difference))
						outputs.append((str(uuid.uuid1()),new_transaction.transaction_id,receiver,amount))                                             # the money to be given to receiver
						
						
						new_transaction.inputs=inputs                                                 # add the trasaction inputs
						new_transaction.outputs=outputs          		              	              # add the transaction outputs	
						new_transaction.sign_transaction()											  # sign transaction	
						
						#threading.Thread(target=self.broadcast_transaction, args=(new_transaction,)).start()	 # broadcast to all nodes, should it be called by new thread??
						#threading.Thread(target=asyncio.run,args=(self.broadcast_transaction(new_transaction),)).start()
						#broadcast_thread.start()    
						print(new_transaction)  
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

	def transaction_sending(*args):
		_,node_,trans_to_broadcast=args
		
		
		try:
			res=requests.post('{}/transactions/receive'.format(node_['contact']), json=trans_to_broadcast)
			if (res.status_code==200):                                     # transaction sent
				print('transaction sent to node:', node_['node_id'])						
			else:                                                          # error in sending
				print("error sending transaction to node:", node_['node_id'], res.json()['message'])
		except:
			print("error2 sending transaction to node:", node_['node_id'])




	async def broadcast_transaction(self,transaction,to_all=True):
		trans_to_broadcast=transaction.to_dict(True)
		#print(trans_to_broadcast)
		if to_all:
			for node_ in self.ring:
				#sent_thread=threading.Thread(target=self.persistent_sending,args=(node_,trans_to_broadcast))
				sent_thread=threading.Thread(target=self.transaction_sending,args=(node_,trans_to_broadcast))
				sent_thread.start()
		else:
			node_=self.ring[0]
				#sent_thread=threading.Thread(target=self.persistent_sending,args=(node_,trans_to_broadcast))
			sent_thread=threading.Thread(target=self.transaction_sending,args=(node_,trans_to_broadcast))
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
				self.locks['NBCs'].acquire()
				for input in transaction.inputs:                     # check that every input is unspent
					found_utxo=False
					for utxo in self.NBCs[sender_id]:          
						if utxo[0]==input[0]:
							found_utxo=True
							self.NBCs[sender_id].remove(utxo)
					if not found_utxo:
						print('utxo not unspent')
						self.locks['NBCs'].release()
						return False
				
			# add transaction outputs to UTXOs list (NBCs)
				
				for output in transaction.outputs:                 # inputs unspent, time to add outputs to NBCs list
					for item in self.ring:                         # find id of node whose wallter will get the NBCs
						if output[2]==item['address']:
							print('found node id',item['node_id'])
							node_id=item['node_id']
					if node_id==None:
						print('Node id not found in ring')
						self.locks['NBCs'].release()
						return False
					if output not in self.NBCs[node_id]:
						self.NBCs[node_id].append(output)
					#print('new nbcs:', self.NBCs)
				self.locks['NBCs'].release()
			self.locks['valid_trans'].acquire()
			self.valid_transaction_ids.add(transaction.transaction_id)
			self.locks['valid_trans'].release()
			return True                                         
		except:
			return False



	async def send_blockchain(self):							     # function for bootstrap to send blockchain_to_nodes
		block_list=[]
		self.locks['chain'].acquire()
		for i in range(0,len(self.chain)):					 # create list of blocks in sendable form
			block_list.append(self.chain[i].to_dict(True))
		self.locks['chain'].release()
		data=block_list
		num=[0]						   						# variable to hold how many nodes have received the ring
		for node_ in self.ring[1:]:       					    # send ring to all nodes in ring
			t=threading.Thread(target=self.persistent_sending_blockchain_to_nodes, args=(node_,data,num))     # new thread for each node, call insinde function for the rest of the functionality
			t.start()


	def persistent_sending_blockchain_to_nodes(self,*args):
			node_,data,num=args
			sent=False
			while(not sent):																# try to send ring until succesful
				try:
					res=requests.post('{}/blockchain/get'.format(node_['contact']), json=data)
					if (res.status_code==200):                                              # ring sent
						print('blockchain sent to node:', node_['node_id'])			
						sent=True	
						num[0]+=1															# increase number of nodes that have received the ring
						if (num[0]==len(self.ring)-1):                                        # if all nodes have received the ring, time to broadcast blockchain
							print("all nodes have received blockchain")

							message,error_code,trans=self.create_transaction(self.wallet.address,self.ring[-1]['address'],100)
							threading.Thread(target=asyncio.run,args=(self.broadcast_transaction(trans,False),)).start()
							
							if error_code!=200:
								return message, error_code
							print('after creation')

							#self.add_transaction_to_block(trans)


					else:                                                                   # error in sending
						print("error sending blockchain to node:", node_['node_id'], res.json()['message'])
						sent=False
						
						
				except:
					print("error2 sending blockchain to node:", node_['node_id'])
					sent=False
					



	def persistent_sending_ring_to_nodes(self,*args):
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
						
						print("all nodes have reiced ring")

						# all nodes have received ring, time to broadcast blockchain
						t=threading.Thread(target=asyncio.run, args=(self.send_blockchain(),))
						t.start()
				else:                                                                   # error in sending
					print("error sending ring to node:", node_['node_id'], res.json()['message'])
					sent=False
					
			except:
				print("error2 sending ring to node:", node_['node_id'])
				sent=False
				
				

	def send_data_to_nodes_give_blockchain(self):                                      
		# function for the bootstrap to send to the nodes the ring, the blockchain so far, and to create and send the initial transactions
		data={"ring": self.ring}       # data to send at first is the ring
		num=[0]						   # variable to hold how many nodes have received the ring
		for node_ in self.ring:        # send ring to all nodes in ring
			t=threading.Thread(target=self.persistent_sending_ring_to_nodes, args=(node_,data,num))     # new thread for each node, call insinde function for the rest of the functionality
			t.start()
			
	
	# def make_transfer(self):                   # function to transfer 100 NBCs from the bootstrap node to all the other nodes of the ring
	# 	for node_ in self.ring:                # for every node in the ring:
	# 		if node_['node_id']==0:            # except from bootstrap
	# 			print('not for bootstrap')
	# 			continue
	# 		message,error_code,trans=self.create_transaction(self.wallet.address,node_['address'],100)
	# 		if error_code!=200:
	# 			return message,error_code,False
	# 		print('finished',node_['node_id'])		


	def add_transaction_to_block(self,transaction):
		#if enough transactions  mine
		self.locks['cur_block'].acquire()
		if self.current_block==None:
			print("creating new block",transaction)
			self.locks['chain'].acquire()
			if self.chain==[]:                                            # case of genesis block
				self.current_block=self.create_new_block(0,1,None,1)
			elif len(self.chain)==1:									  # case of initial transactions from bootstrap, they will be a block	
				self.current_block=self.create_new_block(self.chain[-1].index+1, self.chain[-1].hash, None, self.node_number-1)
			else:
				self.current_block=self.create_new_block(self.chain[-1].index+1, self.chain[-1].hash, None, self.block_capacity)  # usual case, create next current block following the last of the blockchain
			self.locks['chain'].release()
		self.current_block.listOfTransactions.append(transaction)
		if len(self.current_block.listOfTransactions)==self.current_block.capacity:
			print("block is full")
			#t=threading.Thread(target=asyncio.run, args=(self.mine_block(self.current_block),))
			#threading.Thread(target=asyncio.run,args=(self.mine_block(self.current_block),)).start()
			try:
				t=threading.Thread(target=asyncio.run, args=(self.mine_block(copy.copy(self.current_block)),))
				t.start()
			except Exception as e:
				print(e)
				self.locks['cur_block'].release()
				return
			self.current_block=None
		self.locks['cur_block'].release()
		return


	async def mine_block(self,block_to_mine):

		# start mining
		print("mining block")
		#block_to_mine.nonce=0	
		block_to_mine.nonce=random.randint(0,10000000000000)														# set initial nonce
		while not block_to_mine.myHash().startswith('0'*block_to_mine.difficulty):      # keep trying hashing with a different once until number of zeros specified is reached
			#block_to_mine.nonce+=1	
			block_to_mine.nonce=random.randint(0,10000000000000)									
			# should we be checking if a bloack is already in its place in the chain or if a transaction in the block is already included in a different block?
			
			# check that transactions have not already been included to blockchain by a different node
			self.locks['chain'].acquire()
			print(self.chain)
			if self.chain!=[] and self.chain[-1].index>=block_to_mine.index: 					# check if new block has been added
				print('CASEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
				for block_item in self.chain[block_to_mine.index:]:			# for all new added blocks
					for trans in block_item.listOfTransactions:				# for all transactions of the blocks
						i=0
						while(i<len(block_to_mine.listOfTransactions)):
						# check if they exist in the block beeing mined
							if trans.transaction_id==block_to_mine.listOfTransactions[i].transaction_id:
								block_to_mine.listOfTransactions.pop(i)             # if yes, remove them from block being mined
								i-=1
								if len(block_to_mine.listOfTransactions)==0:		# if no more transactions in block, stop mining
									print("stoping block mining, all transactions already mined")
									self.locks['chain'].release()
									return	
								else:												# otherwise mining will continue
									block_to_mine.index=self.chain[-1].index+1      # correct block index
									block_to_mine.previousHash=self.chain[-1].hash  # correct previous hash
									#block_to_mine.nonce=0							# restart nonce		
									block_to_mine.nonce=random.randint(0,10000000000000)
							i+=1
																					
									
			self.locks['chain'].release()
		print('block mined')

		# mining finished, time to broadcast block to all nodes (if we already have a completed ring)

		# if ring is not completed we are at initialization stage (bootstrap node), block straight to blockchain
		if len(self.ring)<self.node_number:
			print("nodes not here yet, no block broadcast")
			self.locks['chain'].acquire()
			self.chain.append(block_to_mine)                                           # add block straight to chain, it will be shared with the nodes later
																					   # should the chain object the Blockchain or a list?
			self.locks['chain'].release()
		# otherwise, all nodes are in the ring: normal case, mined block has to be broadcasted
		if len(self.ring)==self.node_number:
			print("all nodes here, normal case")
			threading.Thread(target=asyncio.run,args=(self.broadcast_block(block_to_mine),)).start()


		return



	def block_sending(*args):
			_,node_,block_to_broadcast=args
						
			try:
				res=requests.post('{}/blocks/receive'.format(node_['contact']), json=block_to_broadcast)
				if (res.status_code==200):                                     # block sent
					print('block sent to node:', node_['node_id'])						
				else:                                                          # error in sending
					print("error sending block to node:", node_['node_id'], res.json()['message'])
			except:
				print("error2 sending block to node:", node_['node_id'])


	async def broadcast_block(self, block):
		block_to_broadcast=block.to_dict(True)
		for node_ in self.ring:
			#sent_thread=threading.Thread(target=self.persistent_sending,args=(node_,block_to_broadcast))
			sent_thread=threading.Thread(target=self.block_sending,args=(node_,block_to_broadcast))
			sent_thread.start()
		return


	def update_ring_amounts(self):
		for i in range(0,len(self.ring)):
			self.ring[i]['balance']=self.wallet.balance(self.NBCs[i])

	def validate_block(self,block):
		#print(block.listOfTransactions)
		load_dotenv()
		#print(os.getenv('DIFFICULTY'))
		if block.myHash().startswith('0'*int(os.getenv('DIFFICULTY'))):  # check that block hash is correct
			#should check previous hash here
			print(self.chain)
			print('hash ok')
			for trans in block.listOfTransactions:
				if trans.transaction_id not in self.valid_transaction_ids:
					if self.validate_transaction(trans):
						print('valid trans')
					else:
						print('not valid trans')
				else:
					print('transaction already validated')
			self.update_ring_amounts()
			return True
		else:
			print('hash not ok')
			threading.Thread(target=asyncio.run, args=(self.resolve_conflicts(),)).start()
			return False
   
		

	#def valid_proof(.., difficulty=MINING_DIFFICULTY):




	#concencus functions

	def valid_chain(self, chain):
		#check for the longer chain accroose all nodes
		for block in chain:
			if self.validate_block(block):
				print('block valid')
			else:
				print('block not valid')
				return False
		return True

	def resolve_conflicts(self):
		#resolve correct chain
		lengths=[]
		for node_ in self.ring:
			res=requests.get(node_['contact']+'/blockchain/length')
			if res.status_code==200:
				res=res.json()
				print(res)
				lengths.append((node_['node_id'],res['length']))
		max_len=0
		max_id=0
		for item in lengths:
			if item[1]>max_len:
				max_len=item[1]
				max_id=item[0]
		if max_id!=self.id:
			print('new blockchain to be adopted')
			# here wee should call the node to give us its blockchain!!!!!!!!!!!
			# there are some issues: 
			# should we ask for the whole blockchain?
			# how will the NBCs be adapted? 
			# one solution is to get whole blockchain and NBCs or to not get NBCs and calculate everything from the blockchain, but this is not very efficient!
		return


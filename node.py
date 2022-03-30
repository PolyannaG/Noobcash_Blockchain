from ast import excepthandler
from binascii import a2b_hex
import binascii
from cmath import e
from platform import node
from queue import Empty
import random
import sys
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

		self.time_of_mine=None       # time of last last completed mine of a block
		self.time_to_append=[]       # list to hold the time it has taken between the creation of a block and the moment it is appended to the blockchain

		# Locks for different resources
		NBCs_lock=threading.RLock()
		valid_transactions_lock=threading.RLock()
		cur_block_lock=threading.RLock()
		chain_lock=threading.RLock()
		conflict_lock=threading.RLock()
		self.locks={'NBCs': NBCs_lock,'valid_trans': valid_transactions_lock,'cur_block': cur_block_lock,'chain': chain_lock, 'conf': conflict_lock}


		self.block_capacity=5    # capacity of blocks
		
		
		self.chain=[]			 # the blockchain
		self.current_id_count=0  # used by bootstrap to count how many nodes it has registered
		self.node_number=None    # number of nodes in ring
		
		self.id=None	# node id in ring
		self.NBCs={}    # dictionary to hold unspent UTXOs of all nodes:
						# NBCs[i] will be a list that holds transaction outputs (transactions from which the
						# node i has received money)
		
		self.wallet=self.create_wallet()    # wallet is created
		self.ring=[]    				    # here we store information for every node: its id, its contact info (ip:port), its wallet address, its public key and its balance
		self.current_block=None             # the block at which new transactions are beeing appended
		self.pending_transaction_ids=set()  # set to keep pending transactions
		self.used_nbcs=set()				# set to keep NBCs used a inputs in pending transactions
		self.get_back=set()                 # set to keep outputs that are the money the node will get back from the transactions


		self.blocks_mined=0                 # number of blocks the node has mined
		self.transactions_read=0            # number of transactions the node has read from file
		self.transactions_created=[]        # transactions the node has created
		self.transactions_done=[]           # transactions the node created and are added to blockchain
		
		
		#print("creating new node instance")



	def create_new_block(self,index,previousHash,nonce,capacity=5):
		#print("creating new block")
		new_block=Block(index,previousHash,nonce,capacity)			# initialize new block
		return new_block

	def create_wallet(self):
		#create a wallet for this node, with a public key and a private key
		return wallet()
		

	def register_node_to_ring(self,public_key,address, contact):
		#add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
		#bottstrap node informs all other nodes and gives the request node an id and 100 NBCs
		try: 
			node_info={'node_id': self.current_id_count+1,'contact':contact, 'address': address, 'public_key': public_key, 'balance': 0}  # node info
			self.current_id_count+=1      # increase the number of nodes registered
			self.ring.append(node_info)   # add node info to ring
			return True
		except:
			return False


	def sleeper(self):
		#print("sleeping")
		time.sleep(2)
		return

	def create_transaction(self,sender, receiver,amount, signature=None):
		if (sender=='0'):                                  			  # transaction for genesis block	
			new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)
			new_transaction.transaction_inputs=[]
			new_transaction.outputs=[(str(uuid.uuid1()),new_transaction.transaction_id,binascii.b2a_hex(receiver).decode('utf-8'),amount)]
			new_transaction.sign_transaction()
			return 'Transaction created succesfully', 200, new_transaction
		else:                      					    # usual case
			sender_id = None
			for node_item in self.ring:					# check that sender node is indeed part of the ring
				if (node_item['address']==sender):
					sender_id=node_item['node_id']

			receiver_id = None
			for node_item in self.ring:				    # check that receiver node is indeed part of the ring
				if (node_item['address']==receiver):
					receiver_id=node_item['node_id']


			if sender_id==None:						
				return "Sender not part of ring." ,400, None
			elif receiver_id == None:
				return "Receiver not part of ring." ,400, None
			elif sender_id!=self.id: 				  # check that the node is indeed the current one (for safety, should always be true)
				return "Sender not current node, you do not own this wallet.", 400, None
			else:
				self.locks['NBCs'].acquire()
			
				total=self.wallet.balance(self.NBCs[sender_id])	# calculate node's balance its from UTXOs
				for item in self.used_nbcs:                     # true balance is the balance calculated minus outputs of pending transactions
					total-=item[3]

				# check that the node has enough NBCs for the transaction	
				if (total<amount):        # total not enough
					temp_length=len(self.pending_transaction_ids)
					if temp_length==0:    # no pending transactions
						#print('no pending transactions')
						self.locks['NBCs'].release()
						return "Not enough NBCs for the specified transaction.", 400, None
					else:                # there are pending transactions
						self.locks['NBCs'].release()
						while True:      
							self.locks['NBCs'].acquire()
							total=self.wallet.balance(self.NBCs[sender_id])		# get balance		
							for item in self.used_nbcs:	                        # calculate true balance
								total-=item[3]
							# calculate how many money the node is excpecting from pending transactions:
							sum_=0							
							for item in self.get_back:
								sum_+=item[3]
							if total+sum_<amount:                               # if balance plus total is not enough for the transaction, do not do it
								self.locks['NBCs'].release()
								return "Not enough NBCs for the specified transaction.", 400, None

							if temp_length==len(self.pending_transaction_ids) and total<amount:   # if the number of penfing transactions has not changes and the true balance is not enough, sleep and check later
								self.locks['NBCs'].release()
								t=threading.Thread(target=self.sleeper)
								t.start()
								t.join()
								continue

							# if pending, check if you have enough
							# total=self.wallet.balance(self.NBCs[sender_id])
							# for item in self.used_nbcs:	
							# 	total-=item[3]
							if total<amount:           # if length of pending transactions has changes and total still is not enough:
								self.locks['NBCs'].release()
								temp_length=len(self.pending_transaction_ids)
								if temp_length==0:     # if there are no more pending transactions:
									return "Not enough NBCs for the specified transaction.", 400, None  # do not do the transaction
								# otherwise we will check again for changes (busy wait)
							else:  # total is now enough for the transaction, no more waiting, it is time to do it
								break
				
			    # all checks complete, we are ready to start the transaction
				try:
					inputs=[]
					outputs=[]																		
					cur_sum=0
					
					for item in self.NBCs[sender_id]:		# find the previous outputs the money will come from
						if item not in self.used_nbcs:      # use as many outputs as needed
							cur_sum+=item[3]
							inputs.append(item)
							self.used_nbcs.add(item)
							if cur_sum>=amount:
								break
						else:
							continue
					
					difference=cur_sum-amount              # calculate money to get back from transaction
					
					new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)   # create the trascaction
					if (difference!=0):
						out=(str(uuid.uuid1()),new_transaction.transaction_id,sender,difference)  # the output with money to get back
						outputs.append(out)
						self.get_back.add(out)
					out2=(str(uuid.uuid1()),new_transaction.transaction_id,receiver,amount)        # the ouptut with money to be given to receiver
					outputs.append(out2)                                                      
					
					new_transaction.inputs=inputs                                                 # add the trasaction inputs
					new_transaction.outputs=outputs          		              	              # add the transaction outputs	
					new_transaction.sign_transaction()											  # sign transaction	
					
					self.locks['NBCs'].release()
						
					self.pending_transaction_ids.add(new_transaction.transaction_id)              # add transaction to pending
					self.transactions_created.append((new_transaction.transaction_id,new_transaction.amount))  #  add transaction id and amount to created
					return "Transaction created successfully", 200 , new_transaction
				except:  
					self.locks['NBCs'].release()   
					# Case of unexpected error
					return "Error creating transaction.", 500, None


	def transaction_sending(*args):       # function to senf transaction to specified node
		_,node_,trans_to_broadcast=args
		try:
			res=requests.post('{}/transactions/receive'.format(node_['contact']), json=trans_to_broadcast)
		except:
			True


	async def broadcast_transaction(self,transaction,to_all=True):   # funtion to broadcast transaction to all nodes
		trans_to_broadcast=transaction.to_dict(True)                 # get transaction in dictionary form (sendable)
		if to_all:                                                   # broadcast to all nodes
			for node_ in self.ring:
				sent_thread=threading.Thread(target=self.transaction_sending,args=(node_,trans_to_broadcast))
				sent_thread.start()
		else:                                                        # broadcast only to bootstrap
			node_=self.ring[0]
			sent_thread=threading.Thread(target=self.transaction_sending,args=(node_,trans_to_broadcast))
			sent_thread.start()
		

	def validate_transaction(self,transaction,from_resolve_conflict=False):    # function to validate received transaction
		sender_address=a2b_hex(transaction.sender_address)
		key=RSA.importKey(sender_address)                              # public key of sender is the sender's address
		signature=a2b_hex(transaction.signature)	
		trans_to_hash=str(transaction.to_dict())
		hashed_transaction=SHA.new(trans_to_hash.encode('utf-8'))      # hash transaction to verify its signature
		
		try:	
			# signature verification
			is_verified=PKCS1_v1_5.new(key).verify(hashed_transaction,signature)  # verify transaction signature			

			if is_verified:                       # transaction signature validated, now we check UTXOs
				
			# check that transaction inputs are unspent
				for item in self.ring:            # find sender id
					if transaction.sender_address==item['address']:
						sender_id=item['node_id']
						
				if not from_resolve_conflict:
					self.locks['NBCs'].acquire()
				for input in transaction.inputs:   # check that every input is unspent
					found_utxo=False
					for utxo in self.NBCs[sender_id]:          
						if utxo[0]==input[0]:
							found_utxo=True
					if not found_utxo:               # input is not unspent output, transaction is not valid
						#print('utxo not unspent')
						# if invalid transaction is pending of this node remove it, it will not be added to blockchain 
						if transaction.transaction_id in self.pending_transaction_ids:

							for input_ in transaction.inputs:
								if input_ in self.used_nbcs:
									self.used_nbcs.remove(input_)
							for output_ in self.outputs:
								if output_ in self.get_back:
									self.get_back.remove(output_)

						self.pending_transaction_ids.remove(transaction.transaction_id)
						
						if not from_resolve_conflict:
							self.locks['NBCs'].release()
						return False
				
				if not from_resolve_conflict:
					self.locks['NBCs'].release()
			
			# transaction is valid, return True		
			return True                                         
		except:
			if not from_resolve_conflict:
				self.locks['NBCs'].release()
			return False

	def update_nbcs(self,transaction,from_resolve_conflict=False):   # function to update UTXO list (self.NBCs), according to a new transaction
		if not from_resolve_conflict:
			self.locks['NBCs'].acquire()
		sender_id=self.id
		for item in self.ring:                                        # find sender address in ring
			if transaction.sender_address==item['address']:
				sender_id=item['node_id']

		for input in transaction.inputs:                     #  remove inputs from UTXOs
			for utxo in self.NBCs[sender_id]:          
				if utxo[0]==input[0]:
					self.NBCs[sender_id].remove(utxo)
				
		for output in transaction.outputs:                 # add outputs to NBCs list
				for item in self.ring:                     # find id of node whose wallet will get the NBCs
					if output[2]==item['address']:
						node_id=item['node_id']
				if node_id==None:
					#print('Node id not found in ring')
					self.locks['NBCs'].release()
					return False
				if output not in self.NBCs[node_id]:     # add outputs to list of UTXOs
					self.NBCs[node_id].append(output)
				
		if not from_resolve_conflict:	
			self.locks['NBCs'].release()
		


	async def send_blockchain(self):				        # function for bootstrap to send blockchain_to_nodes
		block_list=[]
		self.locks['chain'].acquire()
		for i in range(0,len(self.chain)):					 # create list of blocks in sendable form
			block_list.append(self.chain[i].to_dict(True))
		self.locks['chain'].release()
		data=block_list
		num=[0]						   						# variable to hold how many nodes have received the ring
		for node_ in self.ring[1:]:       					# send blockchain to all nodes in ring
			t=threading.Thread(target=self.persistent_sending_blockchain_to_nodes, args=(node_,data,num))     # new thread for each node, call insinde function for the rest of the functionality
			t.start()


	def persistent_sending_blockchain_to_nodes(self,*args):
			node_,data,num=args
			sent=False
			while(not sent):																# try to send blockchain until succesful
				try:
					res=requests.post('{}/blockchain/get'.format(node_['contact']), json=data)
					if (res.status_code==200):                                              # blockchain sent
						print('blockchain sent to node:', node_['node_id'])			
						sent=True	
						num[0]+=1															# increase number of nodes that have received the ring
						if (num[0]==len(self.ring)-1):                                      # if all nodes have received the ring, create final transaction for the last node and broadcast it
							print("all nodes have received blockchain")

							message,error_code,trans=self.create_transaction(self.wallet.address,self.ring[-1]['address'],100)
							threading.Thread(target=asyncio.run,args=(self.broadcast_transaction(trans,False),)).start()
							if error_code!=200:
								return message, error_code
					else:                                                                   # error in sending
						#print("error sending blockchain to node:", node_['node_id'], res.json()['message'])
						sent=False
						
						
				except:
					#print("error2 sending blockchain to node:", node_['node_id'])
					sent=False
					

	def persistent_sending_ring_to_nodes(self,*args):              # function to send ring to all nodes, and afterwards call function to send blockchain
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
		# function for the bootstrap to send to the nodes the ring, the blockchain so far, and to create and send the last of the initial transactions
		data={"ring": self.ring}       # data to send at first is the ring
		num=[0]						   # variable to hold how many nodes have received the ring
		for node_ in self.ring:        # send ring to all nodes in ring
			t=threading.Thread(target=self.persistent_sending_ring_to_nodes, args=(node_,data,num))     # new thread for each node, call insinde function for the rest of the functionality
			t.start()
				


	def add_transaction_to_block(self,transaction,capacity=None):     # function to add a validated transaction to a block to be mined
		self.locks['chain'].acquire()
		self.locks['cur_block'].acquire()
		is_first = False                 # variable to hold whether transaction added is the first of the block
		if self.current_block==None:     # there is no block with some transactions already, create new one
			is_first = True
			#print("creating new block",transaction)
			
			if self.chain==[]:                                            # case of genesis block
				self.current_block=self.create_new_block(0,1,None,1)
			elif capacity!=None:									      # case of capacity scecified expicitly	
				self.current_block=self.create_new_block(self.chain[-1].index+1, self.chain[-1].hash, None, capacity)
			else:
				self.current_block=self.create_new_block(self.chain[-1].index+1, self.chain[-1].hash, None, self.block_capacity)  # usual case, create next current block following the last of the blockchain
		
		self.locks['chain'].release()
		self.current_block.listOfTransactions.append(transaction)         # add transaction to list of transactions in the block
		if len(self.current_block.listOfTransactions)==self.current_block.capacity or time.time()-self.current_block.timestamp>5:  # if block is full or the block has timed out, time to mine
			try:
				t=threading.Thread(target=asyncio.run, args=(self.mine_block(copy.copy(self.current_block)),))
				t.start()
			except Exception as e:
				print(e)
				self.locks['cur_block'].release()
				return
			self.current_block=None
			self.locks['cur_block'].release()
		else:
			# block is not timed out and is not full, no mine
			self.locks['cur_block'].release()
			if is_first:
				t=threading.Thread(target=asyncio.run, args=(self.check_for_mine(),))   # create thread to watch for block timeout
				t.start()
		return

	async def check_for_mine(self):     # function to check whether the current block to which transactions are beeing added has timed out
		while True:
			#print('checking for mine')
			self.locks['cur_block'].acquire()
			if self.current_block!=None and time.time()-self.current_block.timestamp>5 and len(self.current_block.listOfTransactions)!=0: # if block is not empty and has timed out, time to mine
				t=threading.Thread(target=asyncio.run, args=(self.mine_block(copy.copy(self.current_block)),))
				t.start()
				self.current_block=None
				self.locks['cur_block'].release()
				return
			self.locks['cur_block'].release()
			time.sleep(3)


	async def mine_block(self,block_to_mine):   # function to mine a block
	
		if len(block_to_mine.listOfTransactions)==0:  # if block has no transactions stop mining
			return
	
		block_to_mine.nonce=random.randint(0,10000000000000)				            # set initial nonce. random choice
		while not block_to_mine.myHash().startswith('0'*block_to_mine.difficulty):      # keep trying hashing with a different once until number of zeros specified is reached
			
			if len(block_to_mine.listOfTransactions)==0:                                # if block has no transactions, return
				return
			block_to_mine.nonce=random.randint(0,1000000000000000)                      # pick a new nonce									
			
			# check that transactions have not already been included to blockchain by a different node
			self.locks['chain'].acquire()
			if self.chain!=[] and self.chain[-1].index>=block_to_mine.index: 		    # check if new block has been added to blockchain
				for block_item in self.chain[block_to_mine.index:]:						# for all new added blocks
					for trans in block_item.listOfTransactions:							# for all transactions of the blocks
						i=0
						while(i<len(block_to_mine.listOfTransactions)):
						# check if they exist in the block beeing mined
							if trans.transaction_id==block_to_mine.listOfTransactions[i].transaction_id:
								block_to_mine.listOfTransactions.pop(i)             # if yes, remove them from block being mined
								i-=1
								if len(block_to_mine.listOfTransactions)==0:		# if no more transactions in block, stop mining
									#print("stoping block mining, all transactions already mined")
									self.locks['chain'].release()
									return	
							i+=1
			
				block_to_mine.index=self.chain[-1].index+1      # correct block index
				block_to_mine.previousHash=self.chain[-1].hash  # correct previous hash		
				block_to_mine.nonce=random.randint(0,10000000000000)  # pick new random nonce
																						
			self.locks['chain'].release()
		#print('block mined')

		# block is mined
		self.time_of_mine=time.time()    # set time of last mine by the node
		self.blocks_mined+=1             # one more block has been mined

		# mining finished, time to broadcast block to all nodes (if we already have a completed ring)

		# if ring is not completed we are at initialization stage (bootstrap node), block straight to blockchain
		if len(self.ring)<self.node_number:
			print("nodes not here yet, no block broadcast")
			self.locks['chain'].acquire()
			self.chain.append(block_to_mine)                                           # add block straight to chain, it will be shared with the nodes later
																					   # should the chain object the Blockchain or a list?
			
			for trans in block_to_mine.listOfTransactions:                             # remove from pending transactions, remove outputs from used_nbcs etc.
				if trans.transaction_id in self.pending_transaction_ids:
					for input_ in trans.inputs:
						if input_ in self.used_nbcs:
							self.used_nbcs.remove(input_)
					for output_ in trans.outputs:
						if output_ in self.get_back:
							self.get_back.remove(output_)
					self.pending_transaction_ids.remove(trans.transaction_id)
					self.transactions_done.append((trans.transaction_id,trans.amount))
			
			for trans in block_to_mine.listOfTransactions:                            # update list of NBCs
				self.update_nbcs(trans)
			self.locks['chain'].release()
		# otherwise, all nodes are in the ring: normal case, mined block has to be broadcasted
		if len(self.ring)==self.node_number:
			#print("all nodes here, normal case")
			threading.Thread(target=asyncio.run,args=(self.broadcast_block(block_to_mine),)).start()
		
		return


	def block_sending(*args):                   # function to send block to specified node
			_,node_,block_to_broadcast=args		
			try:
				res=requests.post('{}/blocks/receive'.format(node_['contact']), json=block_to_broadcast)
			except:
				True


	async def broadcast_block(self, block):     # function to broadcast block to all nodes
		block_to_broadcast=block.to_dict(True)
		for node_ in self.ring:
			sent_thread=threading.Thread(target=self.block_sending,args=(node_,block_to_broadcast))
			sent_thread.start()
		return


	def update_ring_amounts(self):              # function to update balances of nodes in self.ring, based on self.NBCs
		for i in range(0,len(self.ring)):
			self.ring[i]['balance']=self.wallet.balance(self.NBCs[i])

	def validate_block(self,block,from_resolve_coflict=False):   # function to validate a received block
		load_dotenv()                                            # load environment variables
		if block.myHash().startswith('0'*int(os.getenv('DIFFICULTY'))):  # check that block hash is correct (has right number of zeros in the beginning)
			# block hash correct
			if not from_resolve_coflict:
				self.locks['chain'].acquire()
			
			if len(self.chain)>=1 and block.previousHash!=self.chain[-1].hash:  # check that block is the expected, so previousHash is the hash of the previous block in blockchain
				try:
					self.locks['chain'].release()
					self.locks['NBCs'].release()
				except:
					try:
						self.locks['NBCs'].release()
					except:
						True


				# previousHash is differnt from the hash of the previous block in blockchain: Conflict!!!

				self.locks['conf'].acquire()
				if block.index<self.chain[-1].index or block.hash==self.chain[-1].hash:  # block earlier in chain, conflict already solved, no need to solve again
					self.locks['conf'].release()
					try:
						self.locks['chain'].release()
						self.locks['NBCs'].release()
					except:
						try:
							self.locks['NBCs'].release()
						except:
							True
					return False

				# Start proccess of resolving conflict:

				#print('-------------------starting resolve conf---------------------------')
				index_to_ask=max(block.index-10,0)     # index of block from which and afterwards the chosen node will send chain
				t=threading.Thread(target=self.resolve_conflicts,args=(index_to_ask,))
				t.start()
				t.join()
				#print('---------------------------ending resolve conf---------------------------')
				#self.resolve_conflicts()
				self.locks['conf'].release()
				return False
			

			# No conflict, block hash valid and previousHash correct

			for trans in block.listOfTransactions:   # check that all transactions are valid
				
				if self.validate_transaction(trans,from_resolve_coflict):
					continue
				else:                                # transaction not valid found: the whole block is invalid
					#print('not valid trans')
					try:
						self.locks['chain'].release()
					except:
						True
					return False
			for trans in block.listOfTransactions:   # all transactions valid, block will be appended to chain, so update NBCs
				self.update_nbcs(trans,True)
			self.update_ring_amounts()               # update ring amounts according to new NBCs
			
			try:
				self.locks['chain'].release()
			except:
				True
			return True
		else:
			#print('hash not ok')
			threading.Thread(target=asyncio.run, args=(self.resolve_conflicts(),)).start()
			return False
   


	#concencus functions

	def restore_nbcs(self,transaction):                      # function to restore NBCs to the way they were before given transaction was accepted
		for item in self.ring:
			if transaction.sender_address==item['address']:
				sender_id=item['node_id']
				#print('found sender in ring',sender_id)
				

		for input in transaction.inputs:                     # add all inputs of transaction back as unspent outputs
			#print(input)
			self.NBCs[sender_id].append(input)
			if sender_id==self.id:
				if input in self.used_nbcs:
					self.used_nbcs.remove(input)	

		for output in transaction.outputs:                 # iremove outputs of transaction from unspent outputs
				for item in self.ring:                        # find id of node whose wallter will get the NBCs
					if output[2]==item['address']:
						node_id=item['node_id']
				if output in self.NBCs[node_id]:
					self.NBCs[node_id].remove(output)
				if node_id==self.id:
					if output in self.get_back:
						self.get_back.remove(output)
		if transaction.transaction_id in self.pending_transaction_ids:
			self.pending_transaction_ids.remove(transaction.transaction_id)


	def resolve_conflicts(self,index):     # function to resolve conflict in chain
		#resolve correct chain
		#print('acquiring locks')
		self.locks['chain'].acquire()
		#print('aq0')
		self.locks['cur_block'].acquire()
		#print('aq1')
		self.locks['NBCs'].acquire()
		#print('aq2')
		self.locks['valid_trans'].acquire()
		#print('aquired locks')
		lengths=[]
		
		for node_ in self.ring:                 # ask all nodes for the length of their blockchain
			res=requests.get(node_['contact']+'/blockchain/length')
			if res.status_code==200:
				res=res.json()
				lengths.append((node_['contact'],res['length']))
		max_len=0
		max_node=0
		for item in lengths:                   # find biggest of all lengths and choose that node
			if item[1]>max_len:
				max_len=item[1]
				max_node=item[0]
		if max_node!=self.ring[self.id]['contact']:
			
			while True:                        # ask chosen node to send blockchain until blockchain is successfully received
				res=requests.get(max_node+'/blockchain/get', params={'index': index})   # index after which the sub-chain will be sent is specified
				if res.status_code==200:
					res=res.json()
					break
			try:
				chain=res['chain']              # sub-chain received
				self.current_block=None         # don't mine old transctions
				old_NBCs=copy.copy(self.NBCs)   


				# find the point after which there is a conflict:

				j=index                         
				while (chain[0]['hash']!=self.chain[j].hash):
					j+=1
				k=0
				while (k<len(chain) and j<len(self.chain) and chain[k]['hash']==self.chain[j].hash):
					k+=1
					j+=1
					
				# pointer in old chain and in new sub-chain that shows point of conflict specified
				if j<len(self.chain):
					thrown_away=self.chain[j:]      # get part of old chain to be thrown away
					#print(thrown_away)
					self.chain=self.chain[:j]       # get part of old chain to be kept
					for block in thrown_away:       # restore NBCs for all transactions in blocks to be thrown away
						for trans in block.listOfTransactions:
							self.restore_nbcs(trans)
				
				# process all new blocks and append them to chain:
				for i in range(k,len(chain)):
					
					processed_block=self.process_block(chain[i])     # convert to object from dictionary
					
					if i==0:                                         # genesis block, not validated. just update NBCs
						for item in processed_block.listOfTransactions:
							try:
								self.update_nbcs(item,True)
							except :
								#print('error in first block')
								self.locks['chain'].release()
								self.locks['cur_block'].release()
								self.locks['NBCs'].release()
								self.locks['valid_trans'].release()
								#print('error in genesis block')
								self.NBCs=copy.copy(old_NBCs)
								self.resolve_conflicts(index)
								return 
					else:                                           # normal case, block must be validated
						if not self.validate_block(processed_block,True):   # block not valid, this and all following will not be added to blockchain, start proccess of resolving conflict again
							print('found block not valid in blockchain')
							try:
								self.locks['chain'].release()
								self.locks['cur_block'].release()
								self.locks['NBCs'].release()
								self.locks['valid_trans'].release()
							except:
								self.locks['cur_block'].release()
								self.locks['NBCs'].release()
								self.locks['valid_trans'].release()
							print('error in block: ',i)
							self.NBCs=copy.copy(old_NBCs)
							self.resolve_conflicts(index)
							return
					self.chain.append(processed_block)           # block valid, append block to chain

					for trans in processed_block.listOfTransactions:    # remove transactions from pending, update used_nbcs etc.
						if trans.transaction_id in self.pending_transaction_ids:

							for input_ in trans.inputs:
								if input_ in self.used_nbcs:
									self.used_nbcs.remove(input_)
							for output_ in trans.outputs:
								if output_ in self.get_back:
									self.get_back.remove(output_)
							self.pending_transaction_ids.remove(trans.transaction_id)
							self.transactions_done.append((trans.transaction_id,trans.amount))
					
					
		            		      
			except e:
				print(e)
				#print('error in resolve conficts')
				self.locks['chain'].release()
				self.locks['cur_block'].release()
				self.locks['NBCs'].release()
				self.locks['valid_trans'].release()
				self.resolve_conflicts(index)
				self.NBCs=copy.copy(old_NBCs)
				return
		self.update_ring_amounts()                          # update ring with new balances
		try:
			self.locks['chain'].release()
			self.locks['cur_block'].release()
			self.locks['NBCs'].release()
			self.locks['valid_trans'].release()		
		except:
			self.locks['cur_block'].release()
			self.locks['NBCs'].release()
			self.locks['valid_trans'].release()
		return


	def process_transaction(self,item):                      # function to convert transaction from dictionary form to object
		try:
			sender_address=item['sender_address']
			receiver_address=item['receiver_address']
			amount=item['amount']
			transaction_id=item['transaction_id']
			transaction_inputs=item['transaction_inputs']
			transaction_outputs=item['transaction_outputs']
			signature=item['signature']
			
			# correct datatypes
			inputs=[]
			for item in transaction_inputs:
				input=(tuple(item))
				inputs.append(input)
				
			outputs=[]
			for item in transaction_outputs:
				output=tuple(item)
				outputs.append(output)

			
			# create transaction object
			trans=Transaction(sender_address,None,receiver_address,amount)
			trans.transaction_id=transaction_id
			trans.inputs=inputs
			trans.outputs=outputs
			trans.signature=signature

			return trans
		except:
			return None

	def process_block(self,data):                                 # function to convert block from dictionary form to object
		try:
			previous_hash=data['previous_hash']
			index=data['index']
			timestamp=data['timestamp']
			list_of_transactions=data['list_of_transactions']
			nonce=data['nonce']
			hash=data['hash']
			capacity=data['capacity']

			proccessed_transaction_list=[]                              # list to add all transactions of block in object form
			for item in list_of_transactions:                           # convert all transaction objects back to object form                
				trans=self.process_transaction(item)
				if trans==None:
					return {'message': "Error in receiving block"}, 400
				proccessed_transaction_list.append(trans)
			new_block=self.create_new_block(index,previous_hash,nonce,capacity)
			new_block.timestamp=timestamp
			new_block.hash=hash
			new_block.listOfTransactions=proccessed_transaction_list
			return new_block
		except:
			return None

	def send_blockchain_resolve_conflict(self,index):               # function to send blockchain to node
		block_list=[]
		self.locks['chain'].acquire()
		for i in range(int(index),len(self.chain)):					 # create list of blocks in sendable form
			block_list.append(self.chain[i].to_dict(True))
		self.locks['chain'].release()
		return block_list


	def view_transaction(self):
		my_chain = self.chain
		if my_chain == []:
			return None
		else:
			last_valid_block = my_chain[-1]
			res = last_valid_block.to_dict(True)
			return res
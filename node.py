from ast import excepthandler
from binascii import a2b_hex
import binascii
from cmath import e
#from msvcrt import locking
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
		#self.NBC=100;
		##set

		NBCs_lock=threading.RLock()
		valid_transactions_lock=threading.RLock()
		cur_block_lock=threading.RLock()
		chain_lock=threading.RLock()
		conflict_lock=threading.RLock()
		self.locks={'NBCs': NBCs_lock,'valid_trans': valid_transactions_lock,'cur_block': cur_block_lock,'chain': chain_lock, 'conf': conflict_lock}


		self.block_capacity=1
		
		
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
		
		self.pending_transaction_ids=set()
		self.used_nbcs=set()
		self.get_back=set()

		#self.trans_pool=set()


		self.blocks_mined=0
		self.transactions_read=0
		self.transactions_created=[]
		self.transactions_done=[]
		self.transactions_denied=[]
		
		print("creating new node instance")



	def create_new_block(self,index,previousHash,nonce,capacity=5):
		#print("creating new block")
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


	def sleeper(self):
		print("sleeping")
		time.sleep(2)
		
		return

	def create_transaction(self,sender, receiver,amount, signature=None):
		#remember to broadcast it
		
		#logic missing!  broadcast !!!!
		if (sender=='0'):
			#print('hereeeeeeee')	
			#print(amount)																		  # transaction for genesis block	
			new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)
			new_transaction.transaction_inputs=[]
			#new_transaction.transaction_outputs=[(receiver,amount)]
			new_transaction.outputs=[(str(uuid.uuid1()),new_transaction.transaction_id,binascii.b2a_hex(receiver).decode('utf-8'),amount)]
			new_transaction.sign_transaction()
			
			

			return 'Transaction created succesfully', 200, new_transaction
		
		else:   
			#print('creating transaction')                        									  # usual case
			
			for node_item in self.ring:																  # check that node is indeed part of the ring
				if (node_item['address']==sender):
					sender_id=node_item['node_id']
			#print(sender_id)
			if sender_id==None:						
				return "Sender not part of ring." ,400, None
			elif sender_id!=self.id:
				print(self.id, sender_id)																  # check that the node is indeed the current one (for safety, should always be true)
				return "1Sender not current node, you do not own this wallet.", 400, None
			else:
				self.locks['NBCs'].acquire()
			
				
				total=self.wallet.balance(self.NBCs[sender_id])	
				
				print(total)
				

				for item in self.used_nbcs:
					
					total-=item[3]
				
				
				if total<amount:
					print(total)
					print(amount)
					print(self.get_back)
					print(self.used_nbcs)

				#print(self.NBCs)									  # check that the node has enough NBCs for the transaction	
				
				if (total<amount):
					print('total not enough')
					# self.locks['NBCs'].release()
					# return "Not enough NBCs for the spesified transaction.", 400, None
					temp_length=len(self.pending_transaction_ids)
					if temp_length==0:
						print('no pending transactions')
						self.locks['NBCs'].release()
						return "2Not enough NBCs for the specified transaction.", 400, None
					else:
						self.locks['NBCs'].release()
						while True:
							print('waitingg')
							
							# if no pending exit
							# if len(self.pending_transaction_ids)==0 and:
							# 	return "Not enough NBCs for the specified transaction.", 400, None
							self.locks['NBCs'].acquire()
							total=self.wallet.balance(self.NBCs[sender_id])				
							for item in self.used_nbcs:	
								total-=item[3]
							
							print(len(self.pending_transaction_ids))
							print(total,amount)

							sum_=0
							for item in self.get_back:
								sum_+=item[3]
							if total+sum_<amount:
								self.locks['NBCs'].release()
								print('not enough for trans, exiting trans')
								return "2.3Not enough NBCs for the specified transaction.", 400, None

							if temp_length==len(self.pending_transaction_ids) and total<amount:
								#time.sleep(2)
								self.locks['NBCs'].release()
								t=threading.Thread(target=self.sleeper)
								t.start()
								t.join()
								print('joined')
								continue

							# if pending, check if you have enough
							# total=self.wallet.balance(self.NBCs[sender_id])
							# for item in self.used_nbcs:	
							# 	total-=item[3]
							if total<amount:
								self.locks['NBCs'].release()
								# if not, sleep
								print('total still not enogh')
								temp_length=len(self.pending_transaction_ids)
								if temp_length==0:
									return "2.5Not enough NBCs for the specified transaction.", 400, None
								#time.sleep(2)
							else:
								print('we can move on with our transaction')
								#self.locks['NBCs'].acquire()
								break
							

						
				
				
				                                                                                 # all checks complete, we are ready to start the transaction
				try:
					#print('heloooo')

					inputs=[]
					outputs=[]																		
					cur_sum=0
					
					for item in self.NBCs[sender_id]:											  # find the previous transactions the money will come from
						if item not in self.used_nbcs:
							cur_sum+=item[3]
							inputs.append(item)
							self.used_nbcs.add(item)
							if cur_sum>=amount:
								break
						else:
							continue
					
					
					# self.locks['NBCs'].release()
					difference=cur_sum-amount
					if difference<0:
						print('------------------------------')													  # calculate how much money the sender has to get back				
						print('------------------------------------------------------------------------------------------')
						print('------------------------------------------------------------------------------------')
						print(len(self.pending_transaction_ids))
						print(total)
						print('------------------------------------------------------------------------------------------')
						print('------------------------------------------------------------------------------------')
					new_transaction=Transaction(sender,self.wallet.private_key,receiver,amount)   # create the trascaction
					if (difference!=0):
						out=(str(uuid.uuid1()),new_transaction.transaction_id,sender,difference)
						outputs.append(out)
						self.get_back.add(out)
					out2=(str(uuid.uuid1()),new_transaction.transaction_id,receiver,amount)
					outputs.append(out2)                                             # the money to be given to receiver
					
					
					
					
					new_transaction.inputs=inputs                                                 # add the trasaction inputs
					new_transaction.outputs=outputs          		              	              # add the transaction outputs	
					new_transaction.sign_transaction()											  # sign transaction	
					

					

					self.locks['NBCs'].release()

						
					self.pending_transaction_ids.add(new_transaction.transaction_id)

					self.transactions_created.append((new_transaction.transaction_id,new_transaction.amount))
					
					return "3Transaction created successfully", 200 , new_transaction
				except:  
					self.locks['NBCs'].release()   
					print('hereeeeeeeeeeeeeeeee')                                                                      # Case of unexpected error
					return "4Error creating transaction.", 500, None


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
				sent_thread=threading.Thread(target=self.transaction_sending,args=(node_,trans_to_broadcast))
				sent_thread.start()
		else:
			node_=self.ring[0]
				#sent_thread=threading.Thread(target=self.persistent_sending,args=(node_,trans_to_broadcast))
			sent_thread=threading.Thread(target=self.transaction_sending,args=(node_,trans_to_broadcast))
			sent_thread.start()


			
						


	def validate_transaction(self,transaction,from_resolve_conflict=False):                       # in what form will the transaction be received here? if it is received as dictionary, we have to make changes
		#use of signature and NBCs balance

		

		#print('validating')		
		sender_address=a2b_hex(transaction.sender_address)
		key=RSA.importKey(sender_address)                              # public key of sender is the sender's address
		#print('key imported')
		signature=a2b_hex(transaction.signature)	
		trans_to_hash=str(transaction.to_dict())
		hashed_transaction=SHA.new(trans_to_hash.encode('utf-8'))      # hash transaction to verify its signature
		
		try:	
			
			# signature verification
			# signature=a2b_hex(transaction.signature)
			# print('signature')
			is_verified=PKCS1_v1_5.new(key).verify(hashed_transaction,signature)  # verify transaction signature			

			if is_verified:                                          # transaction signature validated, now we check UTXOs
				#print('verified singature')
			# check that transaction inputs are unspent
				for item in self.ring:
					if transaction.sender_address==item['address']:
						sender_id=item['node_id']
						#print('found sender in ring',sender_id)
				if not from_resolve_conflict:
					self.locks['NBCs'].acquire()
				for input in transaction.inputs:                     # check that every input is unspent
					found_utxo=False
					for utxo in self.NBCs[sender_id]:          
						if utxo[0]==input[0]:
							found_utxo=True
							#self.NBCs[sender_id].remove(utxo)
					if not found_utxo:
						print('utxo not unspent')
						
						
						if transaction.transaction_id in self.pending_transaction_ids:

							for input_ in transaction.inputs:
								if input_ in self.used_nbcs:
									self.used_nbcs.remove(input_)
							for output_ in self.outputs:
								if output_ in self.get_back:
									self.get_back.remove(output_)

						self.pending_transaction_ids.remove(transaction.transaction_id)
						self.transactions_denied.append((transaction.transaction_id,transaction.amount))
						
						
						if from_resolve_conflict:
							print(self.NBCs[sender_id])
							print('input', input)
						if not from_resolve_conflict:
							self.locks['NBCs'].release()
						return False
				#print('found utxo')
				if not from_resolve_conflict:
					self.locks['NBCs'].release()
			# add transaction outputs to UTXOs list (NBCs)
				
			
			return True                                         
		except:
			if not from_resolve_conflict:
				self.locks['NBCs'].release()
			return False

	def update_nbcs(self,transaction,from_resolve_conflict=False):
		if not from_resolve_conflict:
			self.locks['NBCs'].acquire()
		sender_id=self.id
		for item in self.ring:
			if transaction.sender_address==item['address']:
				sender_id=item['node_id']
				#print('found sender in ring',sender_id)
				

		for input in transaction.inputs:                     # check that every input is unspent
			#print(input)
			for utxo in self.NBCs[sender_id]:          
				if utxo[0]==input[0]:
					self.NBCs[sender_id].remove(utxo)
				

		for output in transaction.outputs:                 # inputs unspent, time to add outputs to NBCs list
				for item in self.ring:                         # find id of node whose wallter will get the NBCs
					if output[2]==item['address']:
						#print('found node id',item['node_id'])
						node_id=item['node_id']
				if node_id==None:
					#print('Node id not found in ring')
					self.locks['NBCs'].release()
					return False
				if output not in self.NBCs[node_id]:
					self.NBCs[node_id].append(output)

				
		if not from_resolve_conflict:	
			self.locks['NBCs'].release()
		


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
				


	def add_transaction_to_block(self,transaction,capacity=None):
		#if enough transactions  mine
		self.locks['chain'].acquire()
		self.locks['cur_block'].acquire()
		if self.current_block==None:
			print("creating new block",transaction)
			
			if self.chain==[]:                                            # case of genesis block
				self.current_block=self.create_new_block(0,1,None,1)
			elif capacity!=None:									  # case of initial transactions from bootstrap, they will be a block	
				self.current_block=self.create_new_block(self.chain[-1].index+1, self.chain[-1].hash, None, capacity)
			else:
				self.current_block=self.create_new_block(self.chain[-1].index+1, self.chain[-1].hash, None, self.block_capacity)  # usual case, create next current block following the last of the blockchain
		
		self.locks['chain'].release()
		self.current_block.listOfTransactions.append(transaction)
		if len(self.current_block.listOfTransactions)==self.current_block.capacity or time.time()-self.current_block.timestamp>5:
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
		else:
			print('to mineeeeeeeeeee')
			self.locks['cur_block'].release()
			t=threading.Thread(target=asyncio.run, args=(self.check_for_mine(),))
			t.start()
		
		return

	async def check_for_mine(self):
		while True:
			#print('checking for mine')
			self.locks['cur_block'].acquire()
			if self.current_block!=None and time.time()-self.current_block.timestamp>5 and len(self.current_block.listOfTransactions)!=0:
				t=threading.Thread(target=asyncio.run, args=(self.mine_block(copy.copy(self.current_block)),))
				t.start()
				self.current_block=None
				self.locks['cur_block'].release()
				return
			self.locks['cur_block'].release()
			time.sleep(3)


	async def mine_block(self,block_to_mine):

		# start mining
		print("mining block")
		if len(block_to_mine.listOfTransactions)==0:
			return

		#block_to_mine.nonce=0	
		block_to_mine.nonce=random.randint(0,10000000000000)														# set initial nonce
		while not block_to_mine.myHash().startswith('0'*block_to_mine.difficulty):      # keep trying hashing with a different once until number of zeros specified is reached
			#block_to_mine.nonce+=1	
			if len(block_to_mine.listOfTransactions)==0:
				return
			block_to_mine.nonce=random.randint(0,1000000000000000)									
			# should we be checking if a bloack is already in its place in the chain or if a transaction in the block is already included in a different block?
			
			# check that transactions have not already been included to blockchain by a different node
			self.locks['chain'].acquire()
			#print(self.chain)
			if self.chain!=[] and self.chain[-1].index>=block_to_mine.index: 					# check if new block has been added
				print('CASEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
				print(self.chain[-1].index,block_to_mine.index)
				for block_item in self.chain[block_to_mine.index:]:			# for all new added blocks
					for trans in block_item.listOfTransactions:				# for all transactions of the blocks
						i=0
						while(i<len(block_to_mine.listOfTransactions)):
						# check if they exist in the block beeing mined
							if trans.transaction_id==block_to_mine.listOfTransactions[i].transaction_id:
								print('popping')
								block_to_mine.listOfTransactions.pop(i)             # if yes, remove them from block being mined
								i-=1
								if len(block_to_mine.listOfTransactions)==0:		# if no more transactions in block, stop mining
									print("stoping block mining, all transactions already mined")
									self.locks['chain'].release()
									
									return	
								# else:												# otherwise mining will continue
								# 	block_to_mine.index=self.chain[-1].index+1      # correct block index
								# 	block_to_mine.previousHash=self.chain[-1].hash  # correct previous hash
								# 	#block_to_mine.nonce=0							# restart nonce		
								# 	block_to_mine.nonce=random.randint(0,10000000000000)
							i+=1
			
				block_to_mine.index=self.chain[-1].index+1      # correct block index
				block_to_mine.previousHash=self.chain[-1].hash  # correct previous hash
				#block_to_mine.nonce=0							# restart nonce		
				block_to_mine.nonce=random.randint(0,10000000000000)
																					
									
			self.locks['chain'].release()
		print('block mined')
		self.blocks_mined+=1

		# mining finished, time to broadcast block to all nodes (if we already have a completed ring)

		# if ring is not completed we are at initialization stage (bootstrap node), block straight to blockchain
		if len(self.ring)<self.node_number:
			print("nodes not here yet, no block broadcast")
			self.locks['chain'].acquire()
			self.chain.append(block_to_mine)                                           # add block straight to chain, it will be shared with the nodes later
																					   # should the chain object the Blockchain or a list?
			
			for trans in block_to_mine.listOfTransactions:
				if trans.transaction_id in self.pending_transaction_ids:
					for input_ in trans.inputs:
						if input_ in self.used_nbcs:
							self.used_nbcs.remove(input_)
					for output_ in trans.outputs:
						if output_ in self.get_back:
							self.get_back.remove(output_)
					self.pending_transaction_ids.remove(trans.transaction_id)
					self.transactions_done.append((trans.transaction_id,trans.amount))
			
			for trans in block_to_mine.listOfTransactions:
				self.update_nbcs(trans)
			self.locks['chain'].release()
		# otherwise, all nodes are in the ring: normal case, mined block has to be broadcasted
		if len(self.ring)==self.node_number:
			print("all nodes here, normal case")
			threading.Thread(target=asyncio.run,args=(self.broadcast_block(block_to_mine),)).start()

		
		return



	def block_sending(*args):
			_,node_,block_to_broadcast=args
						
			try:
				print("sending to node", node_['node_id'])
				res=requests.post('{}/blocks/receive'.format(node_['contact']), json=block_to_broadcast)
				#print('sent', node_['node_id'])
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

	def validate_block(self,block,from_resolve_coflict=False):
		#print(block.listOfTransactions)
		load_dotenv()
		#print(os.getenv('DIFFICULTY'))
		if block.myHash().startswith('0'*int(os.getenv('DIFFICULTY'))):  # check that block hash is correct
			#should check previous hash here
			#print(self.chain)
			#print('hash ok')
			if not from_resolve_coflict:
				self.locks['chain'].acquire()
			
			if len(self.chain)>=1 and block.previousHash!=self.chain[-1].hash:
				#print(block.previousHash)
				#print(self.chain[-1])
				print('errrrrrrrrrrrrrrrrrrrrrrrrrrror', block.index)
				if from_resolve_coflict:
					print('from resolve')
				#threading.Thread(target=asyncio.run, args=(self.resolve_conflicts(),)).start()
				
				# if not from_resolve_coflict:
				# 	self.locks['chain'].release()
				# else:
				# 	self.locks['chain'].release()
				try:
					self.locks['chain'].release()
					self.locks['NBCs'].release()
				except:
					try:
						self.locks['NBCs'].release()
					except:
						True


				

				self.locks['conf'].acquire()
				if block.index<self.chain[-1].index or block.hash==self.chain[-1].hash:
					print('no need to rerolve')
					# for trans in block.listOfTransactions:
					# 	if trans.transaction_id in self.pending_transaction_ids:

					# 		for input_ in trans.inputs:
					# 			if input_ in self.used_nbcs:
					# 				self.used_nbcs.remove(input_)

					# 		self.pending_transaction_ids.remove(trans.transaction_id)
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
				print('-------------------starting resolve conf---------------------------')
				index_to_ask=max(block.index-10,0)
				
				t=threading.Thread(target=self.resolve_conflicts,args=(index_to_ask,))
				t.start()
				t.join()
				print('---------------------------ending resolve conf---------------------------')
				#self.resolve_conflicts()
				self.locks['conf'].release()
				return False
			# else:
			# 	if not from_resolve_coflict:
			# 		self.locks['chain'].release()
			# try:
			# 	self.locks['chain'].release()
			# except:
			# 	True
			for trans in block.listOfTransactions:
				
				if self.validate_transaction(trans,from_resolve_coflict):
					#print('valid trans')
					self.update_nbcs(trans,True)
				else:
					print('not valid trans')
					try:
						self.locks['chain'].release()
					except:
						True
					return False
				
			self.update_ring_amounts()
			#if not from_resolve_coflict:
				#self.locks['chain'].release()
			try:
				self.locks['chain'].release()
			except:
				True
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

	def restore_nbcs(self,transaction):
		for item in self.ring:
			if transaction.sender_address==item['address']:
				sender_id=item['node_id']
				#print('found sender in ring',sender_id)
				

		for input in transaction.inputs:                     # check that every input is unspent
			#print(input)
			self.NBCs[sender_id].append(input)
			if sender_id==self.id:
				if input in self.used_nbcs:
					self.used_nbcs.remove(input)
		
				

		for output in transaction.outputs:                 # inputs unspent, time to add outputs to NBCs list
				for item in self.ring:                         # find id of node whose wallter will get the NBCs
					if output[2]==item['address']:
						#print('found node id',item['node_id'])
						node_id=item['node_id']
				if output in self.NBCs[node_id]:
					self.NBCs[node_id].remove(output)
				if node_id==self.id:
					if output in self.get_back:
						self.get_back.remove(output)
		if transaction.transaction_id in self.pending_transaction_ids:
			self.pending_transaction_ids.remove(transaction.transaction_id)


	def resolve_conflicts(self,index):
		#resolve correct chain
		print('acquiring locks')
		self.locks['chain'].acquire()
		print('aq0')
		self.locks['cur_block'].acquire()
		print('aq1')
		self.locks['NBCs'].acquire()
		print('aq2')
		self.locks['valid_trans'].acquire()
		print('aquired locks')
		lengths=[]
		
		for node_ in self.ring:
			res=requests.get(node_['contact']+'/blockchain/length')
			if res.status_code==200:
				res=res.json()
				lengths.append((node_['contact'],res['length']))
		max_len=0
		max_node=0
		for item in lengths:
			if item[1]>max_len:
				max_len=item[1]
				max_node=item[0]
		if max_node!=self.ring[self.id]['contact']:
			print('new blockchain to be adopted')
			# here wee should call the node to give us its blockchain!!!!!!!!!!!
			# there are some issues: 
			# should we ask for the whole blockchain?
			# how will the NBCs be adapted? 
			# one solution is to get whole blockchain and NBCs or to not get NBCs and calculate everything from the blockchain, but this is not very efficient!
			
			
			while True:
				print('sending request to',max_node)
				res=requests.get(max_node+'/blockchain/get', params={'index': index})
				if res.status_code==200:
					res=res.json()
					break
			try:
				# print('acquiring locks')
				# self.locks['chain'].acquire()
				# print('aq0')
				# self.locks['cur_block'].acquire()
				# print('aq1')
				# self.locks['NBCs'].acquire()
				# print('aq2')
				# self.locks['valid_trans'].acquire()
				# print('aquired locks')
				chain=res['chain']
				#self.chain=[]
				self.current_block=None
				print('length of chain received: ',len(chain))

				old_NBCs=copy.copy(self.NBCs)

				j=index
				while (chain[0]['hash']!=self.chain[j].hash):
					j+=1
				print(j)
				k=0
				while (k<len(chain) and j<len(self.chain) and chain[k]['hash']==self.chain[j].hash):
					k+=1
					j+=1
					print(k,j)
					
				print(k)
				if j<len(self.chain):
					thrown_away=self.chain[j:]
					print(thrown_away)
					self.chain=self.chain[:j]
					for block in thrown_away:
						#block=self.process_block(block)
						for trans in block.listOfTransactions:
							self.restore_nbcs(trans)
				#self.NBCs={}
				
				
				
				for i in range(k,len(chain)):
					
					processed_block=self.process_block(chain[i])
					#print('process block:', processed_block.index)
					if i==0:
						for item in processed_block.listOfTransactions:
							try:
								self.update_nbcs(item,True)
								print('updated NBCs')
								# for output in item.outputs:                 # inputs unspent, time to add outputs to NBCs list
									
								# 	#print(node_instance.ring)
								# 	for item in self.ring:                         # find id of node whose wallter will get the NBCs
								# 		if output[2]==item['address']:
								# 			print('found node id',item['node_id'])
								# 			node_id=item['node_id']
								# 	if node_id==None:
								# 		print('Node id not found in ring')
								# 		self.locks['chain'].release()
								# 		self.locks['cur_block'].release()
								# 		self.locks['NBCs'].release()
								# 		self.locks['valid_trans'].release()
								# 		self.resolve_conflicts()
								# 		return
								# 	if output not in self.NBCs[node_id]:
								# 		self.NBCs[node_id].append(output)
							except :
								print('error in first block')
								self.locks['chain'].release()
								self.locks['cur_block'].release()
								self.locks['NBCs'].release()
								self.locks['valid_trans'].release()
								print('error in genesis block')
								self.NBCs=copy.copy(old_NBCs)
								self.resolve_conflicts(index)
								return 
					else:
						if not self.validate_block(processed_block,True):   # block not valid, this and all following will not be added to blockchain
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
					self.chain.append(processed_block)

					for trans in processed_block.listOfTransactions:
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
				print('error in resolve conficts')
				self.locks['chain'].release()
				self.locks['cur_block'].release()
				self.locks['NBCs'].release()
				self.locks['valid_trans'].release()
				self.resolve_conflicts(index)
				self.NBCs=copy.copy(old_NBCs)
				return
		self.update_ring_amounts()
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


	def process_transaction(self,item):
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

	def process_block(self,data):
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

	def send_blockchain_resolve_conflict(self,index):               # function to send blockchain_to_node
		block_list=[]
		self.locks['chain'].acquire()
		for i in range(int(index),len(self.chain)):					 # create list of blocks in sendable form
			block_list.append(self.chain[i].to_dict(True))
		self.locks['chain'].release()
		return block_list




from Crypto.Hash import SHA
import time
import os
from dotenv import load_dotenv




class Block:
	def __init__(self,index,previousHash,nonce,capacity=5):
		##se
		load_dotenv()
		self.index=index
		self.previousHash=previousHash
		self.timestamp=time.time()
		self.hash=None
		self.nonce=nonce
		self.listOfTransactions=[]
		self.capacity=capacity
		self.difficulty=int(os.getenv('DIFFICULTY'))
		
	
	def to_dict(self,add_hash=False):
		"""
        Convert block info to dictionary
        """
		if not add_hash:
			transactions=[]
			for i in range(0, len(self.listOfTransactions)):
				transactions.append(self.listOfTransactions[i].to_dict(True))
			block_dict=({'previous_hash' : self.previousHash,
						'index' : self.index,
						'timestamp' : self.timestamp,
						'list_of_transactions' : transactions,
						'nonce' : self.nonce,
						})
		else:
			transactions=[]
			for i in range(0, len(self.listOfTransactions)):
				transactions.append(self.listOfTransactions[i].to_dict(True))
			block_dict=({'previous_hash' : self.previousHash,
						'index' : self.index,
						'timestamp' : self.timestamp,
						'list_of_transactions' : transactions,
						'nonce' : self.nonce,
						'hash': self.hash,
						'capacity': self.capacity
						})
			
		return block_dict


	def myHash(self):
		#calculate self.hash
		value_to_hash=str(self.to_dict())
		self.hash=SHA.new(value_to_hash.encode('utf-8'))
		self.hash=self.hash.hexdigest()
		#print('self hash',self.hash)
		return self.hash
		


	# def add_transaction(self, transaction, blockchain):
	# 	#add a transaction to the block
	# 	self.listofTransactions.append(transaction)
		

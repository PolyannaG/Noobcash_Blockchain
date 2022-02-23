
import blockchain
from Crypto.Hash import SHA
import time




class Block:
	def __init__(self,index,previousHash,nonce):
		##set
		self.index=index
		self.previousHash=previousHash
		self.timestamp=time.time()
		self.hash=None
		self.nonce=nonce
		self.listOfTransactions=[]
		
	
	def to_dict(self):
		"""
        Convert block info to dictionary
        """
		block_dict=({'previous_hash' : self.previousHash,
					'index' : self.index,
					'timestamp' : self.timestamp,
					'list_of_transactions' : self.listOfTransactions,
					'nonce' : self.nonce})
		return block_dict


	def myHash(self):
		#calculate self.hash
		value_to_hash=self.to_dict()
		self.hash=SHA.new(value_to_hash.encode('utf-8'))
		


	def add_transaction(self, transaction, blockchain):
		#add a transaction to the block
		self.listofTransactions.append(transaction)
		
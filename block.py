from Crypto.Hash import SHA
import time
import os
from dotenv import load_dotenv


class Block:
    def __init__(self, index, previousHash, nonce, capacity=5):
        load_dotenv()  # load environment variables
        self.index = index  # block's index in blockchain
        self.previousHash = previousHash  # previous block's in blockchain hash
        self.timestamp = time.time()  # time of creation
        self.hash = None  # block hash
        self.nonce = nonce  # block's nonce number
        self.listOfTransactions = []  # transactions of the block
        self.capacity = capacity  # max number of transactions the block can have
        self.difficulty = int(
            os.getenv("DIFFICULTY")
        )  # blockchain's difficulty (number of zeros in the beginning)

    def to_dict(
        self, add_hash=False
    ):  # function to convert block to dictionary from object
        if not add_hash:  # do not add the block hash in the dictionary
            transactions = []
            for i in range(0, len(self.listOfTransactions)):
                transactions.append(self.listOfTransactions[i].to_dict(True))
            block_dict = {
                "previous_hash": self.previousHash,
                "index": self.index,
                "timestamp": self.timestamp,
                "list_of_transactions": transactions,
                "nonce": self.nonce,
            }
        else:  # add the block hash
            transactions = []
            for i in range(0, len(self.listOfTransactions)):
                transactions.append(self.listOfTransactions[i].to_dict(True))
            block_dict = {
                "previous_hash": self.previousHash,
                "index": self.index,
                "timestamp": self.timestamp,
                "list_of_transactions": transactions,
                "nonce": self.nonce,
                "hash": self.hash,
                "capacity": self.capacity,
            }
        return block_dict

    def myHash(self):  # function to calculate block's hash
        value_to_hash = str(self.to_dict())
        self.hash = SHA.new(value_to_hash.encode("utf-8"))
        self.hash = self.hash.hexdigest()
        return self.hash

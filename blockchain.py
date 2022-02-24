from transaction import Transaction
from block import Block


class Blockchain():
    def __init__(self):
        self.transactions=[]                        # all validated transactions
        self.chain=[]                               # the chain of blocks

    def get_transactions(self):                     # returns a list of all validated transactions in the blockchain
        transction_list=[]
        for trans in self.transactions:  
            transction=trans.to_dict()              # convert all transactions to dictionary
            transction_list.append(transction)
        return transction_list

    def add_transaction(self,transaction):
        self.transactions.append(transaction)





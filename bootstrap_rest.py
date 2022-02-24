from operator import index
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
from multiprocessing import Process



import block
from node import Node
from blockchain import Blockchain
from wallet import wallet
import transaction

### REST API FOR BOOTSTRAP NODE



app = Flask(__name__)
CORS(app)
blockchain = Blockchain()
node_number=5


#.......................................................................................
@app.before_first_request
def initial():
    #initialize bootstrap node
    node_instance=Node()
    node_instance.id=0

    # create genesis block
    genesis_block=node_instance.create_new_block(1,1,0)                                                                 # create genesis block
    initial_transaction=node_instance.create_transaction(sender='0', receiver=node_instance.wallet.public_key, amount=100*node_number)           # create initial transaction
    blockchain.add_transaction(initial_transaction)
    return



# get all transactions in the blockchain

@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    
    transactions = blockchain.get_transactions()
    response = {'transactions': transactions}
    return jsonify(response), 200


   

# run it once fore every node

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on',n=5)
    args = parser.parse_args()
    port = args.port
        
    app.run(host='127.0.0.1', port=port)
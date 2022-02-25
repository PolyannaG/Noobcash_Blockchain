import argparse
from operator import index
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
import time
from argparse import ArgumentParser
import argparse


import block
from node import Node
from blockchain import Blockchain
from wallet import wallet
import transaction

### REST API FOR BOOTSTRAP NODE

def run_app(port):
    app.run(host='127.0.0.1', port=port)

def initial():
    #initialize bootstrap node
    
    node_instance.id=0

    # create genesis block
    genesis_block=node_instance.create_new_block(1,1,0)                                                                 # create genesis block
    initial_transaction=node_instance.create_transaction(sender='0', receiver=node_instance.wallet.public_key, amount=100*node_number)           # create initial transaction
    blockchain.add_transaction(initial_transaction)

    # create ring and register self
    node_info=[{'node_id': node_instance.id, 'public_key': node_instance.wallet.public_key, 'balance': 100*node_number}]    # IP ADDRESS MISSING!!
    node_instance.current_id_count+=1
    node_instance.ring.append(node_info)
    return

app = Flask(__name__)
CORS(app)
blockchain = Blockchain()
node_number=5
node_instance=Node()

second_thread = threading.Thread(target=initial())
second_thread.start()
second_thread.join()


#.......................................................................................
# @app.before_first_request
# def initial(node_instance):
#     #initialize bootstrap node
#     node_instance=Node()
#     node_instance.id=0

#     # create genesis block
#     genesis_block=node_instance.create_new_block(1,1,0)                                                                 # create genesis block
#     initial_transaction=node_instance.create_transaction(sender='0', receiver=node_instance.wallet.public_key, amount=100*node_number)           # create initial transaction
#     blockchain.add_transaction(initial_transaction)

#     # create ring and register self
#     node_info=[{'node_id': node_instance.id, 'public_key': node_instance.wallet.public_key, 'balance': 100*node_number}]    # IP ADDRESS MISSING!!
#     node_instance.ring.append(node_info)
#     print(node_instance.ring)
#     return



# get all transactions in the blockchain

@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    
    transactions = blockchain.get_transactions()
    response = {'transactions': transactions}
    return jsonify(response), 200

@app.route('/register',methods=['POST'])
def register_node():
    if (node_instance.current_id_count==node_number):   # check if we already have n nodes
        return 'No more nodes can be added', 400
    else:                                               # add node to ring
        try: 
            data=request.get_json()
            print(data)
            public_key=data['public_key']
            address=data['address']
            if node_instance.register_node_to_ring(public_key,address):
                print(len(node_instance.ring))
                return 'Registed to ring', 200
            else:
                return 'Error registering node, try again.', 404
        except:
            return 'Invalid register info', 400 
        

#run it once for every node

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on',n=5)
    args = parser.parse_args()
    port = args.port
   
   
        
    #app.run(host='127.0.0.1', port=port)
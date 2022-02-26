import argparse
from operator import index
from os import abort
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
import time
from argparse import ArgumentParser
import argparse
import sys


import block
from node import Node
from blockchain import Blockchain
from wallet import wallet
import transaction

### REST API FOR BOOTSTRAP NODE

#def run_app(port):
#    app.run(host='127.0.0.1', port=port)

def initial(port):
    #initialize node : get registered to ring
    with app.app_context():
        dict_to_send={'public_key': str(node_instance.wallet.public_key),'address': str(node_instance.wallet.public_key), 'contact': 'http://127.0.0.1:{}/'.format(str(port))}
        res=requests.post('http://127.0.0.1:5000/register', json=dict_to_send)
        if (res.status_code==200):                                     # registration succeeded
            res=res.json()
            node_instance.id=res['node_id']                            # node id is the one given by bootstrap
            print('node has been registered to ring by bootstrap')
        else:                                                          # error in registration
            print('error in regitration:', res.json()['message'])
            sys.exit()
    return


app = Flask(__name__)
CORS(app)
blockchain = Blockchain()
node_number=5
port=4000
node_instance=Node()

second_thread = threading.Thread(target=initial(port))
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
    print(transactions)
    return jsonify(response), 200



#run it once for every node

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on',n=5)
    args = parser.parse_args()
    port = args.port
   
   
        
    #app.run(host='127.0.0.1', port=port)
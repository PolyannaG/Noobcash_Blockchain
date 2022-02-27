import argparse
from operator import index
from os import abort
from turtle import pu
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
from transaction import Transaction
import binascii
### REST API FOR THE REST OF THE NODES

#def run_app(port):
#    app.run(host='127.0.0.1', port=port)

def initial():
    #initialize node : get registered to ring
    with app.app_context():
        pub_key= binascii.b2a_hex(node_instance.wallet.public_key).decode('utf-8')
        dict_to_send={'public_key': pub_key,'address':pub_key, 'contact': 'http://127.0.0.1:{}/'.format(str(port))}
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


#.......................................................................................


# get all transactions in the blockchain

@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    
    transactions = blockchain.get_transactions()
    response = {'transactions': transactions}
    print(transactions)
    return jsonify(response), 200

@app.route('/transactions/receive', methods=['POST'])
def receive_transaction():
    print('receive trans endpoint')
    data=request.get_json()
    try:
        # get trasnaction data
        sender_address=data['sender_address']
        receiver_address=data['receiver_address']
        amount=data['amount']
        transaction_id=data['transaction_id']
        transaction_inputs=data['transaction_inputs']
        transaction_outputs=data['transaction_outputs']
        signature=data['signature']

        
        # correct datatypes
        inputs=[]
        for item in transaction_inputs:
            input=(tuple(item))
            inputs.append(input)
            
        outputs=[]
        for item in transaction_outputs:
            # print(item)
            # temp=item[1:-1].split(',')
            # temp=tuple(temp)
            # output=(temp[0][1:-1],int(temp[1]))
            output=tuple(item)
            outputs.append(output)

        
        # create transaction object
        trans=Transaction(sender_address,None,receiver_address,amount)
        trans.transaction_id=transaction_id
        trans.inputs=inputs
        trans.outputs=outputs
        trans.signature=signature
        print("received transaction")
        try:
            is_valid=node_instance.validate_transaction(trans)
            if (not is_valid):
                print('not valid transaction')
            else:
                print("valid transaction")
        except:
            print("not valid transaction")
        return {'message': "Received"}, 200
    except:
        return {'message': "Error in receiving transaction"}, 400


@app.route('/ring/get', methods=['POST'])
def receive_ring():
    print('receive ring endpoint')
    data=request.get_json()
    
    try:
        # get trasnaction data
        
        node_instance.ring=data['ring']
        return {'message': "Received"}, 200
    except:
        return {'message': "Error in receiving ring"}, 400


#run it once for every node

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
   
    node_instance=Node()

    second_thread = threading.Thread(target=initial())
    second_thread.start()
    second_thread.join()
            
    app.run(host='127.0.0.1', port=port, use_reloader=False)
import argparse
from cmath import e
from operator import index
from os import abort
from platform import node
from turtle import pu
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
import time
from argparse import ArgumentParser
import argparse
import sys
import os
import asyncio


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
node_instance=Node()

#......................................................................................

def process_transaction(item):
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

def process_block(data):
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
            trans=process_transaction(item)
            if trans==None:
                return {'message': "Error in receiving block"}, 400
            proccessed_transaction_list.append(trans)
        new_block=node_instance.create_new_block(index,previous_hash,nonce,capacity)
        new_block.timestamp=timestamp
        new_block.hash=hash
        new_block.listOfTransactions=proccessed_transaction_list
        return new_block
    except:
        return None



#.......................................................................................


# get all transactions in the blockchain

@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    
    transactions = blockchain.get_transactions()
    response = {'transactions': transactions}
    print(transactions)
    return jsonify(response), 200
@app.route('/NBCs/print',methods=['GET'])
def print_nbcs():
    response=node_instance.NBCs
    return jsonify(response), 200
@app.route('/blockchain/print',methods=['GET'])
def print_blockhain():
    response=[]
    for item in node_instance.chain:
        response.append(item.to_dict(True))
    return jsonify(response),200
@app.route('/ring/print',methods=['GET'])
def print_ring():
    return jsonify(node_instance.ring),200

@app.route('/blockchain/length',methods=['GET'])
def get_blockhain_length():
    response={'length': len(node_instance.chain)}
    return jsonify(response),200

@app.route('/resolve_confict',methods=['GET'])
def temp():
    node_instance.resolve_conflicts()
    return {},200

@app.route('/transactions/create',methods=['POST'])
def create_transaction():
    data=request.get_json()
    
    try:
        id=data['id']
        amount=data['amount']
        for node_ in node_instance.ring:
            if node_['node_id']==id:
                print('receiver node address found')
                receiver_address=node_['address']
                print(node_instance.wallet.public_key,receiver_address)
                message,error_code,trans=node_instance.create_transaction(binascii.b2a_hex(node_instance.wallet.public_key).decode('utf-8'),receiver_address,amount)
                if error_code!=200:
                        return message, error_code
                threading.Thread(target=asyncio.run,args=(node_instance.broadcast_transaction(trans),)).start()
                break
        else:
            print('node address not fount')
            return {'message': 'Error creating transaction'}, 404
        return {'message': 'Created transaction'},200
    except:
        return {'message': 'Error creating transaction'}, 404


@app.route('/transactions/receive', methods=['POST'])
def receive_transaction():
    print('receive trans endpoint')
    data=request.get_json()
    try:
        # get trasnaction data
        trans=process_transaction(data)
        if trans==None:
            return {'message': "Error in receiving transaction"}, 400
        print("received transaction")
        try:
            is_valid=node_instance.validate_transaction(trans)
            if (not is_valid):
                print('not valid transaction')
            else:
                print("valid transaction")
                node_instance.add_transaction_to_block(trans)
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
        # get data
        
        node_instance.ring=data['ring']
        node_instance.node_number=len(node_instance.ring)
        for i in range(0,node_instance.node_number):
            node_instance.NBCs[i]=[]
        return {'message': "Received"}, 200
    except:
        return {'message': "Error in receiving ring"}, 400

@app.route('/blockchain/get', methods=['POST'])
def receive_blockchain():
    print('receive blockchain endpoint')
    data=request.get_json()
    try:
        for i in range(0,len(data)):
            #print(i)
            block_to_get=data[i]
            processed_block=process_block(block_to_get)
            if (i!=0):                                                  # genesis block is not validated              
                if not node_instance.validate_block(processed_block):   # block not valid, this and all following will not be added to blockchain
                    print('found block not valid in blockchain')
                    return {'message': 'Blockchain received'}, 200
            else:
                #print('here', processed_block.listOfTransactions[0].outputs)
                for item in processed_block.listOfTransactions:
                    try:
                        for output in item.outputs:                 # inputs unspent, time to add outputs to NBCs list
                            #print(node_instance.ring)
                            for item in node_instance.ring:                         # find id of node whose wallter will get the NBCs
                                if output[2]==item['address']:
                                    print('found node id',item['node_id'])
                                    node_id=item['node_id']
                            if node_id==None:
                                print('Node id not found in ring')
                                return False
                            if output not in node_instance.NBCs[node_id]:
                                node_instance.NBCs[node_id].append(output)
                    except e:
                        print(e)
            node_instance.chain.append(processed_block)                 # block valid, add to blockchain
            return {'message': 'Blockchain received'}, 200
    except:
        return {'message': 'Error in receiving blockchain'}, 400


@app.route('/blocks/receive', methods=['POST'])
def receive_block():
    print('receive block endpoint')
    data=request.get_json()
   # print('data received',data)
    try:
        # get block data
        
        new_block=process_block(data)
        if new_block==None:
            print('new block is none')
            return {'message': "Error in receiving block"}, 400        

        # validate block
        print('time to validate block')
        if node_instance.validate_block(new_block):
            print('block hash valid')
            node_instance.chain.append(new_block)        # block is valid, add to blockchain
            #print(node_instance.chain)
            #print(node_instance.NBCs)
        else:
            print('block hash not valid')
            # should call resolve confict

        return {'message': "Received"}, 200
            
    except e:
        print(e)
        return {'message': "Error in receiving block"}, 400
        


#run it once for every node

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
   
    

    second_thread = threading.Thread(target=initial())
    second_thread.start()
    second_thread.join()
            
    app.run(host='127.0.0.1', port=port, use_reloader=False)
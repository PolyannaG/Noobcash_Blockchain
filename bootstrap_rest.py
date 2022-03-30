import argparse
from cmath import e

from hashlib import new

from operator import index
from platform import node
from urllib import response
import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading
import time
from argparse import ArgumentParser
import argparse
import asyncio
import binascii
import uuid


import block
from node import Node
from blockchain import Blockchain
from wallet import wallet
from transaction import Transaction
import copy
#import logging

### REST API FOR BOOTSTRAP NODE

# def run_app(port):
#     app.run(host='127.0.0.1', port=port)

def initial():
    #initialize bootstrap node
    
    node_instance.id=0

    # create genesis block
    #genesis_block=node_instance.create_new_block(1,1,0)                                                                 # create genesis block
    _,_,initial_transaction=node_instance.create_transaction(sender='0', receiver=node_instance.wallet.public_key, amount=100*node_number)           # create initial transaction
    #node_instance.NBCs[node_instance.id]=[(str(uuid.uuid1()),initial_transaction.transaction_id,binascii.b2a_hex(initial_transaction.receiver_address).decode('utf-8'),initial_transaction.amount)]
    #initial_transaction.outputs=node_instance.NBCs[node_instance.id]
    node_instance.NBCs[node_instance.id]=copy.copy(initial_transaction.outputs)
    node_instance.add_transaction_to_block(initial_transaction)
    #node_instance.chain.append(genesis_block)      # add genesis block to blockchain

    # create ring and register self
    address=binascii.b2a_hex(node_instance.wallet.public_key).decode('utf-8')
    node_info={'node_id': node_instance.id,'contact': 'http://'+node_address+':{}/'.format(port), 'address': address, 'public_key': address,  'balance': 100*node_number}    # IP ADDRESS MISSING!!
    node_instance.ring.append(node_info)
    return

app = Flask(__name__)
CORS(app)
blockchain = Blockchain()
chain_extra=threading.Lock()

#log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)

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

#------------------------------------------------------FRONTEND------------------------------------------------------
@app.route("/homepage")
def front_homepage():
    data = {"id": node_instance.id}
    return data

@app.route("/info")
def front_info():
    data = {"id": node_instance.id}
    return data

@app.route("/transaction", methods = ['GET', 'POST'])
def front_create_transaction():
    return_data = {}
    return_data["id"] = node_instance.id

    if request.method == 'POST':

        req = request.get_json()
        receiver_address = req["address"]
        amount = req["amount"]

        if (node_instance.wallet.address == receiver_address):
            return_data["message"] = "The sender address is the same as the receiver address. Please select a different receiver address."
            return return_data
            
        try:
            message,error_code,trans=node_instance.create_transaction(binascii.b2a_hex(node_instance.wallet.public_key).decode('utf-8'),receiver_address,amount)
            if error_code!=200:
                msg = str(error_code) + " " + str(message)
                return_data["message"] = msg
            else:
                threading.Thread(target=asyncio.run,args=(node_instance.broadcast_transaction(trans),)).start()
                return_data["message"] = "The transaction was conducted successfully"
            return return_data
        
        except:
            return_data["message"] = 'Error while creating transaction'
            return return_data
 
    else:
        return return_data


@app.route("/view")
def front_view():
    last_block = node_instance.view_transaction()
    data = {}
    
    if last_block == None:
        data["none"] = True
        data["id"] = node_instance.id
    else:
        index = last_block["index"]
        hash = last_block["hash"]
        t = last_block["timestamp"]
        transactions_res = []
        for trans in last_block["list_of_transactions"]:
            dict = {}

            dict["id"] = trans["transaction_id"]
            dict["amount"] = trans["amount"]
            sender_addr = trans["sender_address"]
            receiver_addr = trans["receiver_address"]

            for node_ in node_instance.ring:
                if node_['address'] == sender_addr:
                    dict["sender_id"] = node_['node_id']
                if node_['address'] == receiver_addr:
                    dict["receiver_id"] = node_['node_id']

            transactions_res.append(dict)
            
            data["none"] = False
            data["id"]=node_instance.id
            data["index"] = index
            data["hash"] = hash
            data["t"] = t
            data["transactions"] = transactions_res
        
    return data

@app.route("/balance")
def front_balance():
    curr_balance = node_instance.wallet.balance(node_instance.NBCs[node_instance.id])
    data = {}
    data["id"] = node_instance.id
    data["balance"] = curr_balance
    return data

@app.route("/help")
def front_help():     
    data = {"id": node_instance.id}
    return data

#--------------------------------------------------------------------------------------------------------------------

#---------------------------------------------------------CLI---------------------------------------------------------
@app.route("/cli_transaction", methods = ['POST'])
def cli_create_transaction():
    receiver_address = request.form.to_dict()['address']
    amount = int(request.form.to_dict()['amount'])

    if (node_instance.wallet.address == receiver_address):
        return "The sender id is the same as the receiver id. Please select a different receiver id."

    try:
        message,error_code,trans=node_instance.create_transaction(binascii.b2a_hex(node_instance.wallet.public_key).decode('utf-8'),receiver_address,amount)
        if error_code!=200:
            msg = str(error_code) + " " + str(message)
            return msg
        else:
            threading.Thread(target=asyncio.run,args=(node_instance.broadcast_transaction(trans),)).start()
            return "The transaction was conducted successfully"
    
    except:
        return "Error while creating transaction"

@app.route("/cli_view", methods = ['GET'])
def cli_view():
    last_block = node_instance.view_transaction()
    
    if last_block == None:
        return "There is no valid block in the blockchain yet"
    else:
        res = "\n"
        count = 1
        for trans in last_block["list_of_transactions"]:
            transaction = (f"Transaction {count}")
            count += 1
            res = res + transaction + "\n\n" + str(trans) + "\n\n"
        return res

@app.route("/cli_balance", methods = ['GET'])
def cli_balance():
    curr_balance = node_instance.wallet.balance(node_instance.NBCs[node_instance.id])
    return str(curr_balance)

#---------------------------------------------------------------------------------------------------------------------

@app.route('/throughput',methods=['GET'])
def return_time():
    response={
        'time_of_last_mine': node_instance.time_of_mine
    }
    return jsonify(response),200
@app.route('/block_time',methods=['GET'])
def return_append_time():
    response={
        'mean_time_to_append': sum(node_instance.time_to_append)/len(node_instance.time_to_append)
    }
    return jsonify(response),200

@app.route('/data/print',methods=['GET'])
def print_data():
    temp=[]
    for item in node_instance.transactions_created:
        if item not in node_instance.transactions_done:
            temp.append(item)
    #print(node_instance.transactions_read,len(node_instance.transactions_created),len(node_instance.transactions_done))
    
    response={
        'blocks_mined': node_instance.blocks_mined,
        'transactions_read': node_instance.transactions_read,
        'transactions_created': node_instance.transactions_created,
        'transactions_done': node_instance.transactions_done,
        'transactions invalid': node_instance.transactions_denied,
        'in_created_not_done': temp    }
    return jsonify(response), 200

@app.route('/second',methods=['GET'])
def second():
    all_trans=[]
    for block in node_instance.chain:
        for trans in block.listOfTransactions:
            if ((trans.transaction_id,trans.amount)) in node_instance.transactions_created:
                all_trans.append((trans.transaction_id,trans.amount))
    for item in node_instance.transactions_created:
        if item not in all_trans:
            #print(item)
            True
    return {}, 200


@app.route('/file_transactions', methods=['GET'])
def read_file_trans():
    file1 = open('./5nodes/transactions{}.txt'.format(node_instance.id), 'r')
    count = 0
    
    while True:
        #print('new transaction ', count)
        count += 1
    
        # Get next line from file
        line = file1.readline()
        #time.sleep(3)
    
        # if line is empty
        # end of file is reached
        if not line:
            break
        line=line.strip()
        id=line.split()[0]
        id=int(id[2:])
        if id>node_instance.node_number:
            continue
        amount=int(line.split()[1])
        try:
            node_instance.transactions_read+=1
        
            for node_ in node_instance.ring:
                if node_['node_id']==id:
                    #print('receiver node address found')
                    receiver_address=node_['address']
                    #print(node_instance.wallet.public_key,receiver_address)
                    message,error_code,trans=node_instance.create_transaction(binascii.b2a_hex(node_instance.wallet.public_key).decode('utf-8'),receiver_address,amount)
                    if error_code!=200:
                            #print('error creating trans')
                            #print(message)
                            continue
                    #print('crrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr')
                    threading.Thread(target=asyncio.run,args=(node_instance.broadcast_transaction(trans),)).start()
                    
                    break
        except:
            #print('error2 creating trans')
            continue
    
    file1.close()
    return jsonify({}),200

#.......................................................................................


# get all transactions in the blockchain

@app.route('/transactions/print', methods=['GET'])
def get_transactions():
    
    transactions = blockchain.get_transactions()
    response = {'transactions': transactions}
    #print(transactions)
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
    node_instance.update_ring_amounts()
    return jsonify(node_instance.ring),200

@app.route('/blockchain/length',methods=['GET'])
def get_blockhain_length():
    response={'length': len(node_instance.chain)}
    return jsonify(response),200

@app.route('/blockchain/get', methods=['GET'])
def send_blockchain():
    data=request.args
    index=data["index"]
    #print(index)
    response={'chain': node_instance.send_blockchain_resolve_conflict(index)}
    return jsonify(response),200

@app.route('/register',methods=['POST'])
def register_node():
    if (node_instance.current_id_count==node_number-1):   # check if we already have n nodes
        return {'message': 'No more nodes can be added'}, 400
    else:                                               # add node to ring
        try: 
            
            # get data for register and register node

            data=request.get_json()
            public_key=data['public_key']
            address=data['address']
            contact=data['contact']
            if node_instance.register_node_to_ring(public_key,address,contact):
                node_instance.NBCs[node_instance.current_id_count]=[]

                if (node_instance.current_id_count==node_number-1):
                    #print('node ring full')
                    node_instance.send_data_to_nodes_give_blockchain()
                else:                                                      # in the case of the last node of the ring, transaction will be added after ring,blockchain are sent, and block will be mined
                    # create transaction to transfer 100 NBCs
                    message,error_code,trans=node_instance.create_transaction(node_instance.wallet.address,address,100)
                    

                    if error_code!=200:
                        return message, error_code
                    #print('after creation')

                    threading.Thread(target=asyncio.run,args=(node_instance.broadcast_transaction(trans,False),)).start()

                    #node_instance.add_transaction_to_block(trans)
                    
                return {'message:': 'Registed to ring', 'node_id': node_instance.current_id_count}, 200
                
            
            else:
                return {'message:': 'Error registering node, try again.'}, 404
        except e:
            print(e)
            return {'message': 'Invalid register info'}, 400 
        
@app.route('/transactions/receive', methods=['POST'])
def receive_transaction():
    #print('receive trans endpoint')
    data=request.get_json()
    try:
        # get trasnaction data
        trans=process_transaction(data)
        if trans==None:
            return {'message': "Error in receiving transaction"}, 400
        #print("received transaction")
        try:
            is_valid=node_instance.validate_transaction(trans)
            if (not is_valid):
                #print('not valid transaction')
                True
            else:
                #print("valid transaction")
                node_instance.add_transaction_to_block(trans)
        except:
            #print("not valid transaction")
            True
        return {'message': "Received"}, 200
    except:
        return {'message': "Error in receiving transaction"}, 400


@app.route('/ring/get', methods=['POST'])
def receive_ring():
    #print('receive ring endpoint')
    data=request.get_json()
    
    try:
        # get trasnaction data
        
        node_instance.ring=data['ring']
        return {'message': "Received"}, 200
    except:
        return {'message': "Error in receiving ring"}, 400


@app.route('/blocks/receive', methods=['POST'])
def receive_block():
    #print('receive block endpoint')
    data=request.get_json()
   # print('data received',data)
    try:
        # get block data
        
        new_block=process_block(data)
        if new_block==None:
            #print('new block is none')
            return {'message': "Error in receiving block"}, 400        

        # validate block
        #print('time to validate block')
        chain_extra.acquire()
        node_instance.locks['chain'].acquire()
        node_instance.locks['NBCs'].acquire()
        if node_instance.validate_block(new_block,True):
            #print('block hash valid',new_block.index)
            node_instance.chain.append(new_block)        # block is valid, add to blockchain
            node_instance.time_to_append.append(time.time()-new_block.timestamp)

            for trans in new_block.listOfTransactions:
                if trans.transaction_id in node_instance.pending_transaction_ids:

                    for input_ in trans.inputs:
                        if input_ in node_instance.used_nbcs:
                            node_instance.used_nbcs.remove(input_)
                    for output_ in trans.outputs:
                        if output_ in node_instance.get_back:
                            node_instance.get_back.remove(output_)

                    node_instance.pending_transaction_ids.remove(trans.transaction_id)
                    node_instance.transactions_done.append((trans.transaction_id,trans.amount))
                    
            #print(node_instance.chain)
            #print(node_instance.NBCs)
        else:
            #print('block hash not valid')
            True


            # for trans in new_block.listOfTransactions:
            #     if trans.transaction_id in node_instance.pending_transaction_ids:
            #         print('------------------------------------------------------------------------------------------------')
            #         for input_ in trans.inputs:
            #             if input_ in node_instance.used_nbcs:
            #                 node_instance.used_nbcs.remove(input_)
            #         for output_ in trans.outputs:
            #             if output_ in node_instance.get_back:
            #                 node_instance.get_back.remove(output_)
            #         node_instance.pending_transaction_ids.remove(trans.transaction_id)
                    
        try:
            chain_extra.release()
            node_instance.locks['chain'].release()
            node_instance.locks['NBCs'].release()
            
        except:
            try:
               node_instance.locks['NBCs'].release()
            except:
                True
        # try:
        #     node_instance.locks['chain'].release()
        # except:
        #     return {'message': "Received"}, 200
        return {'message': "Received"}, 200
            
    except e:
        print(e)
        return {'message': "Error in receiving block"}, 400








#run it once for every node

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-n', '--nodes', default=5, type=int, help='number of nodes in ring')
    parser.add_argument('-a-', '--address', default='127.0.0.1', type=str, help='node address')

    args = parser.parse_args()
    port = args.port
    node_number=args.nodes
    node_address=args.address
    
    node_instance=Node()
    node_instance.node_number=node_number

    second_thread = threading.Thread(target=initial())
    second_thread.start()
    second_thread.join()
        
    app.run(host=node_address, port=port, use_reloader=False)

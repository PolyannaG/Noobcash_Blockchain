from cmath import e
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
from argparse import ArgumentParser
import sys
import asyncio
from node import Node
from transaction import Transaction
import binascii


def initial():
    # initialize node : get registered to ring
    with app.app_context():
        pub_key = binascii.b2a_hex(
            node_instance.wallet.public_key).decode('utf-8')
        dict_to_send = {'public_key': pub_key, 'address': pub_key,
                        'contact': 'http://'+node_address[0]+':{}/'.format(str(port))}
        res = requests.post(
            'http://'+node_address[1]+':5000/register', json=dict_to_send)
        if (res.status_code == 200):                                     # registration succeeded
            res = res.json()
            # node id is the one given by bootstrap
            node_instance.id = res['node_id']
            print(node_instance.id)
            print('node has been registered to ring by bootstrap')
        else:                                                          # error in registration
            print('error in regitration:', res.json()['message'])
            sys.exit()
    return


app = Flask(__name__)
CORS(app)
node_instance = Node()                  # initialize node instance
chain_extra = threading.Lock()          # lock to be used by program

# ....................................................................................................................


# function to convert transaction from dictionary to class object
def process_transaction(item):
    try:
        sender_address = item['sender_address']
        receiver_address = item['receiver_address']
        amount = item['amount']
        transaction_id = item['transaction_id']
        transaction_inputs = item['transaction_inputs']
        transaction_outputs = item['transaction_outputs']
        signature = item['signature']

        # correct datatypes
        inputs = []
        for item in transaction_inputs:
            input = (tuple(item))
            inputs.append(input)

        outputs = []
        for item in transaction_outputs:
            output = tuple(item)
            outputs.append(output)

        # create transaction object
        trans = Transaction(sender_address, None, receiver_address, amount)
        trans.transaction_id = transaction_id
        trans.inputs = inputs
        trans.outputs = outputs
        trans.signature = signature

        return trans
    except:
        return None


# function to convert block from dictionary to class object
def process_block(data):
    try:
        previous_hash = data['previous_hash']
        index = data['index']
        timestamp = data['timestamp']
        list_of_transactions = data['list_of_transactions']
        nonce = data['nonce']
        hash = data['hash']
        capacity = data['capacity']

        # list to add all transactions of block in object form
        proccessed_transaction_list = []
        # convert all transaction objects back to object form
        for item in list_of_transactions:
            trans = process_transaction(item)
            if trans == None:
                return {'message': "Error in receiving block"}, 400
            proccessed_transaction_list.append(trans)
        new_block = node_instance.create_new_block(
            index, previous_hash, nonce, capacity)
        new_block.timestamp = timestamp
        new_block.hash = hash
        new_block.listOfTransactions = proccessed_transaction_list
        return new_block
    except:
        return None


# ....................................................................................................................

# ------------------------------------------------------FRONTEND------------------------------------------------------
# Endpoints that fetch data that the frontend client (the middleware) requests in order to display in the html pages
# Endpoints that make changes that the frontend client (the middleware) requests

@app.route("/homepage")
def front_homepage():                       # for the homepage we only need to fetch the ID of the node that is currently using the frontend interface
    # return the data in the form of a dictionary
    data = {"id": node_instance.id}
    return data


@app.route("/info")
def front_info():                           # for the team information page we only need to fetch the ID of the node that is currently using the frontend interface
    data = {"id": node_instance.id}
    return data


@app.route("/transaction", methods=['GET', 'POST'])
# for the transaction page we either create a transaction or simply fetch node ID for the page
def front_create_transaction():
    return_data = {}
    # ID of the node currently using the frontend interface (needed in both cases)
    return_data["id"] = node_instance.id

    if request.method == 'POST':            # POST METHOD triggered by the button "Create Transaction" after the input fields are filled
        # returns the node ID (to display on the transaction page) and a suitable message depending on the success of the transaction

        req = request.get_json()
        # get the receiver address from middleware's request
        receiver_address = req["address"]
        # get the amount of noobcash coins to send from middleware's request
        amount = req["amount"]

        # if the sender tries to send coins to itself don't try to create the transaction - return error message
        if (node_instance.wallet.address == receiver_address):
            return_data["message"] = "The sender address is the same as the receiver address. Please select a different receiver address."
            return return_data

        # try to create the transaction
        try:
            message, error_code, trans = node_instance.create_transaction(binascii.b2a_hex(
                node_instance.wallet.public_key).decode('utf-8'), receiver_address, amount)

            if error_code != 200:             # if the transaction fails return error message
                msg = str(error_code) + " " + str(message)
                return_data["message"] = msg
            else:                           # if the transaction succeeds send success message
                threading.Thread(target=asyncio.run, args=(node_instance.broadcast_transaction(
                    trans),)).start()     # broadcast the created transaction to the other nodes
                return_data["message"] = "The transaction was conducted successfully"

            return return_data

        # if the try fails return error message
        except:
            return_data["message"] = 'Error while creating transaction'
            return return_data

    else:                                   # GET METHOD if we simply need to fetch the transaction page
        return return_data                  # return only the node ID and not any message


@app.route("/view")
def front_view():                           # for the view page fetch the node ID, the last valid block's info and the transactions contained in this block
    # Node endpoint to get last valid block
    last_block = node_instance.view_transaction()
    data = {}

    if last_block == None:                  # if there is no valid block
        # boolean that is True if there is no valid block
        data["none"] = True
        data["id"] = node_instance.id

    else:                                   # else if there is a valid block in the current blockchain
        index = last_block["index"]
        hash = last_block["hash"]
        t = last_block["timestamp"]

        transactions_res = []
        # list_of_transactions contained in the last valid block
        for trans in last_block["list_of_transactions"]:
            # each position of the list is a dictionary containing transaction info: id, amount, sender_id, receiver_id
            dict = {}

            dict["id"] = trans["transaction_id"]
            dict["amount"] = trans["amount"]
            sender_addr = trans["sender_address"]
            receiver_addr = trans["receiver_address"]

            # get node ids from the ring using the node addresses that we took from the last valid block
            for node_ in node_instance.ring:
                if node_['address'] == sender_addr:
                    dict["sender_id"] = node_['node_id']
                if node_['address'] == receiver_addr:
                    dict["receiver_id"] = node_['node_id']

            transactions_res.append(dict)

            data["none"] = False
            data["id"] = node_instance.id
            data["index"] = index
            data["hash"] = hash
            data["t"] = t
            data["transactions"] = transactions_res

    # data contains : boolean, node_id, block_index, block_hash, block_creationTime, list_of_transactions
    return data


@app.route("/balance")
def front_balance():                        # for the balance page fetch the the id of the node that is currently using the frontend interface and the balance in this node's wallet
    # wallet endpoint to calculate current balance
    curr_balance = node_instance.wallet.balance(
        node_instance.NBCs[node_instance.id])
    data = {}
    data["id"] = node_instance.id
    data["balance"] = curr_balance
    return data                             # return dictionary with node_ID and balance


@app.route("/help")
def front_help():                           # for the help page we only need to fetch the ID of the node that is currently using the frontend interface
    data = {"id": node_instance.id}
    return data

# --------------------------------------------------------------------------------------------------------------------

# ---------------------------------------------------------CLI---------------------------------------------------------
# Endpoints that fetch data that the cli client requests in order to display after a certain command
# Endpoints that make changes that the cli client requests after a certain command


@app.route("/cli_transaction", methods=['POST'])
def cli_create_transaction():                               # create transaction after t command
    receiver_address = request.form.to_dict()['address']
    amount = int(request.form.to_dict()['amount'])

    # if the sender tries to send coins to itself don't try to create the transaction - return error message
    if (node_instance.wallet.address == receiver_address):
        return "The sender id is the same as the receiver id. Please select a different receiver id."

    # try to create the transaction
    try:
        message, error_code, trans = node_instance.create_transaction(binascii.b2a_hex(
            node_instance.wallet.public_key).decode('utf-8'), receiver_address, amount)
        if error_code != 200:                                 # if the transaction fails return error message
            msg = str(error_code) + " " + str(message)
            return msg
        else:                                               # else if the transaction succeeds send success message
            threading.Thread(target=asyncio.run, args=(node_instance.broadcast_transaction(
                trans),)).start()     # broadcast the created transaction to the other nodes
            return "The transaction was conducted successfully"

    # if the try fails return error message
    except:
        return "Error while creating transaction"


@app.route("/cli_view", methods=['GET'])
# fetch last valid block's transactions after view command
def cli_view():
    # Node endpoint to get last valid block
    last_block = node_instance.view_transaction()

    if last_block == None:                                  # if there is no valid block return error message
        return "There is no valid block in the blockchain yet"
    else:                                                   # else
        res = "\n"
        count = 1
        # create response with all the transactions' contained in the last valid block
        for trans in last_block["list_of_transactions"]:
            transaction = (f"Transaction {count}")
            count += 1
            res = res + transaction + "\n\n" + str(trans) + "\n\n"
        return res


@app.route("/cli_balance", methods=['GET'])
# fetch current node's wallet balance after balance command
def cli_balance():
    # wallet endpoint to calculate current balance
    curr_balance = node_instance.wallet.balance(
        node_instance.NBCs[node_instance.id])
    return str(curr_balance)

# ---------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------BACKEND REST API---------------------------------------------------


# returns time that the last mine occured
@app.route('/throughput', methods=['GET'])
def return_time():
    response = {
        'time_of_last_mine': node_instance.time_of_mine
    }
    return jsonify(response), 200


# returns mean time from creation of block until its addition to the blockchain
@app.route('/block_time', methods=['GET'])
def return_append_time():
    response = {
        'mean_time_to_append': sum(node_instance.time_to_append)/len(node_instance.time_to_append)
    }
    return jsonify(response), 200


# prints some general data about the transations of the node
@app.route('/data/print', methods=['GET'])
def print_data():
    temp = []
    for item in node_instance.transactions_created:
        if item not in node_instance.transactions_done:
            temp.append(item)
    response = {
        'blocks_mined': node_instance.blocks_mined,
        'transactions_read': node_instance.transactions_read,
        'transactions_created': node_instance.transactions_created,
        'transactions_done': node_instance.transactions_done,
        'in_created_not_done': temp}
    return jsonify(response), 200


# second endpoint for general data about the transactions of the node, prints transactions created by this node but not added to blockchain
@app.route('/second', methods=['GET'])
def second():
    all_trans = []
    for block in node_instance.chain:
        for trans in block.listOfTransactions:
            if ((trans.transaction_id, trans.amount)) in node_instance.transactions_created:
                all_trans.append((trans.transaction_id, trans.amount))
    for item in node_instance.transactions_created:
        if item not in all_trans:
            # print(item)
            True
    return {}, 200


# when called, the node reads the transactions of the file transactions{node id}.txt
@app.route('/file_transactions', methods=['GET'])
def read_file_trans():
    try:
        filedirectory = request.args.get("file_directory")
        file1 = open(
            './{}/transactions{}.txt'.format(filedirectory, node_instance.id), 'r')
    except:
        return {'message': 'Error reading transaction file. Check specified file_directory'}, 404
    count = 0
    while True:
        count += 1
        # Get next line from file
        line = file1.readline()
        # if line is empty
        # end of file is reached
        if not line:
            break
        line = line.strip()
        id = line.split()[0]
        id = int(id[2:])
        if id > node_instance.node_number:
            continue
        amount = int(line.split()[1])
        try:
            node_instance.transactions_read += 1

            for node_ in node_instance.ring:            # find node id
                if node_['node_id'] == id:
                    receiver_address = node_['address']
                    message, error_code, trans = node_instance.create_transaction(binascii.b2a_hex(
                        node_instance.wallet.public_key).decode('utf-8'), receiver_address, amount)   # create transaction
                    if error_code != 200:
                        continue
                    threading.Thread(target=asyncio.run, args=(
                        node_instance.broadcast_transaction(trans),)).start()   # broadcast transaction
                    break
        except:
            continue
    file1.close()
    return jsonify({}), 200


# returns node's list of UTXOs
@app.route('/NBCs/print', methods=['GET'])
def print_nbcs():
    response = node_instance.NBCs
    return jsonify(response), 200


# prints the blockchain
@app.route('/blockchain/print', methods=['GET'])
def print_blockhain():
    response = []
    for item in node_instance.chain:
        response.append(item.to_dict(True))
    return jsonify(response), 200


# prints the ring
@app.route('/ring/print', methods=['GET'])
def print_ring():
    node_instance.update_ring_amounts()
    return jsonify(node_instance.ring), 200


# prints blockchain's length
@app.route('/blockchain/length', methods=['GET'])
def get_blockhain_length():
    response = {'length': len(node_instance.chain)}
    return jsonify(response), 200


# returns the blockchain after a specified block index
@app.route('/blockchain/get', methods=['GET'])
def send_blockchain():
    data = request.args
    index = data["index"]
    response = {'chain': node_instance.send_blockchain_resolve_conflict(index)}
    return jsonify(response), 200


# created new transaction
@app.route('/transactions/create', methods=['POST'])
def create_transaction():
    data = request.get_json()
    try:
        # get receiver's id in ring
        id = data['id']
        # get amount
        amount = data['amount']
        for node_ in node_instance.ring:
            if node_['node_id'] == id:
                receiver_address = node_['address']
                message, error_code, trans = node_instance.create_transaction(binascii.b2a_hex(
                    node_instance.wallet.public_key).decode('utf-8'), receiver_address, amount)
                if error_code != 200:
                    return message, error_code
                threading.Thread(target=asyncio.run, args=(
                    node_instance.broadcast_transaction(trans),)).start()
                break
        else:
            return {'message': 'Error creating transaction'}, 404
        return {'message': 'Created transaction'}, 200
    except:
        return {'message': 'Error creating transaction'}, 404


# endpoint called when a transaction is sent to the node
@app.route('/transactions/receive', methods=['POST'])
def receive_transaction():
    data = request.get_json()
    try:
        # get trasnaction data
        trans = process_transaction(data)
        if trans == None:
            return {'message': "Error in receiving transaction"}, 400
        try:
            is_valid = node_instance.validate_transaction(
                trans)              # validate transaction
            # not valid, no addition to block
            if (not is_valid):
                True
            else:
                # valid, will be added to a block
                node_instance.add_transaction_to_block(trans)
        except:
            True
        return {'message': "Received"}, 200
    except:
        return {'message': "Error in receiving transaction"}, 400


# endpoint called for a node to receive a new ring
@app.route('/ring/get', methods=['POST'])
def receive_ring():
    data = request.get_json()
    try:
        # get ring data
        node_instance.ring = data['ring']
        node_instance.node_number = len(node_instance.ring)
        for i in range(0, node_instance.node_number):
            node_instance.NBCs[i] = []
        return {'message': "Received"}, 200
    except:
        return {'message': "Error in receiving ring"}, 400


# endpoint called for a node to receive blockchain by bootstrap
@app.route('/blockchain/get', methods=['POST'])
def receive_blockchain():
    if node_instance.chain != []:
        return {'message': 'Blockchain already received'}, 200
    data = request.get_json()
    try:
        node_instance.locks['chain'].acquire()
        for i in range(0, len(data)):
            block_to_get = data[i]
            processed_block = process_block(block_to_get)
            # genesis block is not validated
            if (i != 0):
                # block not valid, this and all following will not be added to blockchain
                if not node_instance.validate_block(processed_block, True):
                    return {'message': 'Blockchain received'}, 200
            else:                                                            # block valid
                for item in processed_block.listOfTransactions:
                    try:
                        for output in item.outputs:                         # inputs unspent, time to add outputs to NBCs list
                            for item in node_instance.ring:                 # find id of node whose wallet will get the NBCs
                                if output[2] == item['address']:
                                    node_id = item['node_id']
                            if node_id == None:
                                return False
                            if output not in node_instance.NBCs[node_id]:
                                node_instance.NBCs[node_id].append(output)
                            if node_id == node_instance.id:
                                node_instance.myNBCs.append(output)
                    except e:
                        print(e)
            # block valid, add to blockchain
            node_instance.chain.append(processed_block)
        try:
            node_instance.locks['chain'].release()
        except:
            True
        return {'message': 'Blockchain received'}, 200
    except:
        node_instance.locks['chain'].release()
        return {'message': 'Error in receiving blockchain'}, 400


# endpoint called when a block is sent to the node
@app.route('/blocks/receive', methods=['POST'])
def receive_block():
    data = request.get_json()
    try:
        # get block data
        new_block = process_block(data)  # convert to object
        if new_block == None:
            return {'message': "Error in receiving block"}, 400
        # validate block
        chain_extra.acquire()
        node_instance.locks['chain'].acquire()
        node_instance.locks['NBCs'].acquire()
        if node_instance.validate_block(new_block, True):
            # block is valid, add to blockchain
            node_instance.chain.append(new_block)
            # add time between creation and addition to blockchain to list
            node_instance.time_to_append.append(
                time.time()-new_block.timestamp)

            # for all its transactions:
            for trans in new_block.listOfTransactions:
                # if it is one of the node's pending:
                if trans.transaction_id in node_instance.pending_transaction_ids:
                    # remove used NBCs from set of NBCs used as inputs in pending transactions
                    for input_ in trans.inputs:
                        if input_ in node_instance.used_nbcs:
                            node_instance.used_nbcs.remove(input_)
                    # remove outputs from set of excpected outputs to be received
                    for output_ in trans.outputs:
                        if output_ in node_instance.get_back:
                            node_instance.get_back.remove(output_)

                    node_instance.pending_transaction_ids.remove(
                        trans.transaction_id)          # remove from pending transactions
                    node_instance.transactions_done.append(
                        (trans.transaction_id, trans.amount))  # add to list of transctions done
        else:  # block not valid
            True
        try:
            chain_extra.release()
            node_instance.locks['chain'].release()
            node_instance.locks['NBCs'].release()

        except:
            try:
                node_instance.locks['NBCs'].release()
            except:
                True
        return {'message': "Received"}, 200

    except e:
        print(e)
        return {'message': "Error in receiving block"}, 400


# main function, runs in the beggining
if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int,
                        help='port to listen on')               # port the app runs on
    parser.add_argument('-a', '--address', default='127.0.0.1', type=str,
                        help='node address')           # number of nodes in rin
    parser.add_argument('-b', '--bootstrap', default='127.0.0.1',
                        type=str, help='bootstrap address')   # node's local ip address

    args = parser.parse_args()
    port = args.port
    node_address = []
    node_address.append(args.address)
    node_address.append(args.bootstrap)

    second_thread = threading.Thread(target=initial())
    second_thread.start()
    second_thread.join()

    app.run(host=node_address[0], port=port, use_reloader=False)

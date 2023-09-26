# Noobcash_Blockchain

This project implements a distributed cryptocurrency exchange system that uses blockchain. 

Except from the blockchain system implementation, a user interface and a CLI are also included, through which the transactions and wallet balances can be viewed and new transactions can be requested.

## System architecture and functionallity

The system uses two or more nodes. Each node is considered to be a user with a wallet, able to request trancations, as well as a worker, building blocks and participating in the blockchain building process. The transaction request and worker roles are performed in parallel, independently. 

During the system initialization phase, one of the nodes becomes the administrator and is responsible for registering the rest of the nodes to the system (the total number of nodes must be predefined) as well as for creating the first block in the blockchain. On initialization, each node being registered receives an initial amount of 100 coins from the adminstrator. After the initiallization process, the administrator node no longer performs additional functionality and becomes equal to all other nodes. Transactions can start being made after the initialization phase has completed.

## Build

To build the project you can clone the current repository and run:

```bash
pip install -r requirements.txt
````
in a virtual environment.

## Run 

To run the system, you must first raise the administrator node, by running:

```bash
python ./bootstrap_rest.py -n <node_number> -p <port_number>
```
where the number of nodes and the port number can be selected.

Afterwards, you can start raising the rest of the nodes, in a sequential order, by running:

```bash
python ./simplenode_rest.py -p <port_number>
```

for every node, where the port number can again be selected.

### Transaction request

The `5nodes` and `10nodes` folders contain files with a list of transactions for the cases were a system with 5 or with 10 nodes is created. Each file is named as `transactions<node_id>.txt` where `node_id` is the id of one of the nodes, based on the series in which the nodes entered the system during the initialization phase (the administration node has an id equal to 0). You can request for a node to read the transactions that correspond to the node's id by sending a `GET ` request to:
```
http://localhost:<port_number>/file_transactions?file_directory=<transaction directory name>
```
for example:
```
http://localhost:<port_number>/file_transactions?file_directory=5nodes
```

and the node will read the transactions and add them to the list of transactions to be broadcasted and added into blocks of fthe blockchain by all of the system's nodes.

Alternatively, you can request a specific transaction from a node, using a `POST` request to:
```
http://localhost:<port_number>/transactions/create
```
with json data:
```
{
    "id" : <node id>,
    "amount": <amount to sent>
}
```
for example:
```
{
    "id" : 1,
    "amount": 4
}
```

You can print the existing blockchain by sending a `GET` request to:
```
http://localhost:<port_number>/blockchain/print
```

## Using the CLI

Documentation to be added shortly.

## Using the user inteface

Documentation to be added shortly.

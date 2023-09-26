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

The CLI can be run for each of the nodes through th command:
```
python cli.py --port <X> --address <Y> <command>
```
whereby <X> is the port number and <Y> is the IP address the noobcash app is running on for the specific node.

The folllowing commands are available:
* `view` :
    Allows user to see the transactions included in the last block of the blockchain.
* `balance` :
    Allows user to see the current node's balance.
* `t --recipient_address <address> --amount <amount of coins>` :
    Can be used to create a transaction, in order to send `<amount of coins>` to the node with address `<address>`,  from the current node. (The node addresses can be recovered from the blockchain using `view` command for testing purposes).

For each command the `--help` parameter is also available to provide related documentation.

Example usages:
```
python cli.py --port 5001 --address "127.0.0.1" balance
python cli.py --port 5001 --address "127.0.0.1" view
python cli.py --port 5001 --address "127.0.0.1" t  --amount 2 --recipient_address "2d2d2d2d2d424547494e205055424c4943204b45592d2d2d2d2d0a4d494942496a414e42676b71686b6947397730424151454641414f43415138414d49494243674b434151454136623079636e49596c58513950486842345a4b580a6e77587430594f76665344506d5048734246736f79584e61556d4e73426f5763797641376c32484253544f3345645137367a62306b7a765a2f49345861576f790a337a563732557145413664317078393478676b4f4d4550584e7a58687138777a6670617a58307761386a5835627a695a4f6574726f436d47376f5948747243710a585748356f5a6e5073757a62694159556a4e63584e4b34546c71694d4264716431354a47334e65506151525165734137703056787766796e5a505a4d76426e6a0a32416551333071646f4e38354c356557572b59774746303647786a3131323465475a387a784442563267326435664757736146416750655637476854727541310a6d76483953736f504c45447178653930797979426266326167644a664f6a6c506156476275504b56366474445172735259332f2f325661715765734c717472460a53514944415141420a2d2d2d2d2d454e44205055424c4943204b45592d2d2d2d2d"
python cli.py --port 5001 --address "127.0.0.1" view --help
```
## Using the User Interface

The user inteface (UI) app can be run using:
```
python middleware.py --port <MiddlewarePort>
```
where `<MiddlewarePort>` is the desired port number for the UI app to be run (default: `4000`).

After starting the UI app, the UI corresponding to each node can be accessed separately through:
```
http://<IP>:<MiddlewarePort>/homepage/nodeID/<X>
```
where `<IP>` is the address the UI app is running on, and `<X>` is the node ID whose UI one wishes to access.

Example usage:
```
http://127.0.0.1:4001/homepage/nodeID/1
```

Through the UI, one can perform transactions, view the last conducted transaction, view the node's wallet's balance and read some general information about the UI's offered functionalities.

***Note*** The address at which the UI app can access the running nodes is specified as an environment variable named `NODEADDRESS` and is currently set to `localhost`. It can be changed directly from the `.env` file.

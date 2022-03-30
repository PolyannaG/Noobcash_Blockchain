from flask import Flask, render_template, flash, request
from flask_cors import CORS
import socket
import requests
import json

app = Flask(__name__)
CORS(app)
app.secret_key = b'_noobcash5#y2L"F2Blockchain9Q8z\n\xec]/'

def get_contact(id):
    my_ip = socket.gethostbyname(socket.gethostname())
    #ring_url = "http://" + 'localhost:5000/ring/print'
    ring_url = "http://" + str(my_ip) + ':5000/ring/print'
    ring = json.loads((requests.get(ring_url)).text)
    address = None
    for node in ring:
        if int(node["node_id"]) == id:
            address = node["contact"]

    return address


@app.route("/homepage/nodeID/<myid>")
def homepage(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/homepage"
    mydata = json.loads((requests.get(url)).text)
    arg = []
    arg.append(mydata['id'])

    return render_template("homepage.html", data = arg)
    

@app.route("/info/nodeID/<myid>")
def info(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/info"
    mydata = json.loads((requests.get(url)).text)
    arg = []
    arg.append(mydata['id'])

    return render_template("info.html", data = arg)

@app.route("/transaction/nodeID/<myid>", methods = ['GET', 'POST'])
def create_transaction_front(myid):
    node_id = int(myid)
    address = get_contact(node_id)
    
    arg = []

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/transaction"

    if request.method == 'POST':
        receiver_address = request.form.get("address")
        amount = int(request.form.get("amount"))
        post_data = {"address" : receiver_address, "amount" : amount}
        
        mydata = json.loads((requests.post(url, json = post_data)).text)
       
        arg.append(mydata['id'])
        flash(mydata["message"])

        return render_template("create_transaction.html", data = arg)

    else:
        mydata = json.loads((requests.get(url)).text)
        arg.append(mydata['id'])

        return render_template("create_transaction.html", data = arg)



@app.route("/view/nodeID/<myid>")
def view(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/view"
    mydata = json.loads((requests.get(url)).text)
    arg = []

    if mydata["none"] == True:
        arg.append(mydata['id'])

        return render_template("view_none.html", data = arg)
    else:
        arg.append(mydata["id"])
        arg.append(mydata["index"])
        arg.append(mydata["hash"])
        arg.append(mydata["t"])
        arg.append(mydata["transactions"])

        return render_template("view.html", data = arg)

@app.route("/balance/nodeID/<myid>")
def balance(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/balance"
    mydata = json.loads((requests.get(url)).text)
    arg = []
    arg.append(mydata['id'])
    arg.append(mydata['balance'])

    return render_template("balance.html", data = arg)

@app.route("/help/nodeID/<myid>")
def help(myid):     
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/help"
    mydata = json.loads((requests.get(url)).text)
    arg = []
    arg.append(mydata['id'])

    return render_template("help.html", data = arg)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=4000, type=int, help='port to listen on')

    args = parser.parse_args()
    port = args.port
        
    app.run(host='127.0.0.1', port=port, use_reloader=False)
import os
from flask import Flask, render_template, flash, request
from flask_cors import CORS
import socket
import requests
import json
import time

app = Flask(__name__)
CORS(app)
app.secret_key = b'_noobcash5#y2L"F2Blockchain9Q8z\n\xec]/'  # set app secret key in order the flash messages to work

# -------------------------------------------------------------------


def get_contact(id):  # function to get the address of a node, given its ID
    # my_ip = socket.gethostbyname(
    #     socket.gethostname()
    # )
    # get IP address for the current machine to build correct url
    my_ip = os.environ.get("NODEADDRESS")
    ring_url = "http://" + str(my_ip) + ":5000/ring/print"
    ring = json.loads((requests.get(ring_url)).text)  # get the ring
    address = None
    for node in ring:  # check all nodes in ring
        if int(node["node_id"]) == id:  # if you find the given node ID in the ring
            address = node["contact"]  # then get nodes address

    return address


# -------------------------------------------------------------------

# Endpoints that are accessed by the frontend client and contain variable <myid> in their url, which is the ID of the node that is currently using the frontend interface
# All endpoints follow the same logic:
#   1) build dynamically the correct url to access the corresponding endpoint in the rest api of the correct node
#   2) send a request to the above url and get as a response the information that must be displayed in the frontend interface
#   3) render the correct html page with the info we collected from the above request


@app.route("/homepage/nodeID/<myid>")  # Homepage
def homepage(myid):
    node_id = int(myid)
    address = get_contact(
        node_id
    )  # get the contact of the correct node in order to access the correct endpoint in the correct rest api

    if address == None:  # If the node id is not part of the ring
        return render_template(
            "no_node.html"
        )  # render no_node page to inform the user that the node ID he typed in the url does not exist

    url = str(address) + "/homepage"  # build url
    mydata = json.loads(
        (requests.get(url)).text
    )  # get response from the request we sent and make it a json object (from string)

    arg = []
    arg.append(
        mydata["id"]
    )  # create list with response data in order to be able to pass it in the render_template data

    return render_template(
        "homepage.html", data=arg
    )  # render homepage with the correct data we collected from the above request


@app.route("/info/nodeID/<myid>")  # Team information page
def info(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/info"
    mydata = json.loads((requests.get(url)).text)

    arg = []
    arg.append(mydata["id"])

    return render_template("info.html", data=arg)


@app.route(
    "/transaction/nodeID/<myid>", methods=["GET", "POST"]
)  # Transaction page -> create a transaction
def create_transaction_front(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    arg = []

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/transaction"  # build url

    if (
        request.method == "POST"
    ):  # if POST METHOD, "Create Transaction" button has been pushed, we need to create a transaction with the data collected from the form in the frontend
        receiver_address = request.form.get(
            "address"
        )  # get receiver address from the frontend's input form
        amount = int(
            request.form.get("amount")
        )  # get amount of coins to send from frontend's input form
        post_data = {
            "address": receiver_address,
            "amount": amount,
        }  # make them json object in order to be able to pass them in post request

        mydata = json.loads((requests.post(url, json=post_data)).text)

        arg.append(mydata["id"])
        flash(
            mydata["message"]
        )  # flash (show to html frontend page) the return message we got from the endpoint

        return render_template("create_transaction.html", data=arg)

    else:  # else if GET METHOD we simply render the page without creating a new transaction (input form not filled - submit button not pushed)
        mydata = json.loads((requests.get(url)).text)
        arg.append(mydata["id"])

        return render_template("create_transaction.html", data=arg)


@app.route(
    "/view/nodeID/<myid>"
)  # View Page -> see the last valid block's transactions
def view(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/view"
    mydata = json.loads((requests.get(url)).text)

    arg = []

    if mydata["none"] == True:  # if no valid block in the blockchain
        arg.append(mydata["id"])
        return render_template("view_none.html", data=arg)
    else:  # else
        arg.append(mydata["id"])
        arg.append(mydata["index"])
        arg.append(mydata["hash"])
        arg.append(
            time.strftime("%a, %d %b %Y %I:%M:%S %p %Z", time.localtime(mydata["t"]))
        )  # get block creation time in sec and change it in date-time format so that it can be displayed in frontend
        arg.append(mydata["transactions"])

        return render_template("view.html", data=arg)


@app.route(
    "/balance/nodeID/<myid>"
)  # Balance page -> see the wallet balance of the node that currently uses the frontend interface
def balance(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/balance"
    mydata = json.loads((requests.get(url)).text)

    arg = []
    arg.append(mydata["id"])
    arg.append(mydata["balance"])

    return render_template("balance.html", data=arg)


@app.route(
    "/help/nodeID/<myid>"
)  # Help page -> see explanatory information about all the other pages in the frontend interface
def help(myid):
    node_id = int(myid)
    address = get_contact(node_id)

    if address == None:
        return render_template("no_node.html")

    url = str(address) + "/help"
    mydata = json.loads((requests.get(url)).text)

    arg = []
    arg.append(mydata["id"])

    return render_template("help.html", data=arg)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--port", default=4000, type=int, help="port to listen on"
    )
    parser.add_argument(
        "-a", "--address", default="127.0.0.1", type=str, help="machine address"
    )

    args = parser.parse_args()
    port = args.port
    address = args.address

    app.run(host=address, port=port, use_reloader=False)

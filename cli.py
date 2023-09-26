import socket
import requests
import click


# group custom commands
# required option --port to define in which port the current node's app listens to, in order to send the requests in the correct REST API
# pass option --port to all child commands
@click.group()
@click.option(
    "--port", required=True, type=int, help="The port that our application listens to"
)
@click.option(
    "--address", required=True, type=str, help="The address our application listens to"
)
@click.pass_context
def cli(ctx, address, port):
    ctx.ensure_object(dict)
    ctx.obj["port"] = port
    ctx.obj["address"] = address


# All custom commands follow the same logic


@click.command(
    name="t",
    help="The current node sends <amount> of noobcash coins to the node whose address is <recipient_address>",
)
@click.option(
    "--recipient_address",
    required=True,
    type=str,
    help="The address of the node that will receive the specified amount of noobcash coins",
)
@click.option(
    "--amount", required=True, type=int, help="The amount of noobcash coins to be sent"
)
@click.pass_obj
def t(ctx, recipient_address, amount):
    port = ctx["port"]  # get port option from group to build the url
    # my_ip = socket.gethostbyname(
    #     socket.gethostname()
    # )
    # get current machine's IP to build the url
    my_ip = ctx["address"]
    url = (
        "http://" + str(my_ip) + ":" + str(port) + "/cli_transaction"
    )  # build correct url to access the corresponding endpoint to the correct REST API
    click.echo("Transaction pending...")
    req = requests.post(
        url, data={"address": recipient_address, "amount": amount}
    )  # send post request and get the response
    click.echo(req.text)  # show the response to the user


@click.command(
    name="view",
    help="Show the transactions that are contained in the last valid block of the current blockchain",
)
@click.pass_obj
def view(ctx):
    port = ctx["port"]
    # my_ip = socket.gethostbyname(socket.gethostname())
    my_ip = ctx["address"]
    url = "http://" + str(my_ip) + ":" + str(port) + "/cli_view"
    req = requests.get(url)
    click.echo(req.text)


@click.command(name="balance", help="Show the balance of the current node`s wallet")
@click.pass_obj
def balance(ctx):
    port = ctx["port"]
    # my_ip = socket.gethostbyname(socket.gethostname())
    my_ip = ctx["address"]
    url = "http://" + str(my_ip) + ":" + str(port) + "/cli_balance"
    req = requests.get(url)
    click.echo(req.text)


# add custom commands to group
cli.add_command(balance)
cli.add_command(view)
cli.add_command(t)


if __name__ == "__main__":
    cli()

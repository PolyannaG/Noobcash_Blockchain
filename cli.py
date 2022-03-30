import socket
import requests
import click

@click.group()
@click.option('--port', required=True, type=int, help='The port that our application listens to')
@click.pass_context
def cli(ctx, port):
    ctx.ensure_object(dict)
    ctx.obj['port'] = port

@click.command(name='t', help='The current node sends <amount> of noobcash coins to the node whose address is <recipient_address>')
@click.option('--recipient_address', required=True, type=str, help='The address of the node that will receive the specified amount of noobcash coins')
@click.option('--amount', required=True, type=int, help='The amount of noobcash coins to be sent')
@click.pass_obj
def t(ctx,recipient_address, amount):
    port = ctx["port"]
    my_ip = socket.gethostbyname(socket.gethostname())
    #print(my_ip)
    #print(type(my_ip))
    #url = "http://" + 'localhost'+ ":" + str(port) + '/cli_transaction'
    url = "http://" + str(my_ip) + ":" + str(port) + '/cli_transaction'
    click.echo("Transaction pending...")
    req = requests.post(url, data={"address" : recipient_address, "amount": amount})
    click.echo(req.text)

@click.command(name = 'view', help = 'Show the transactions that are contained in the last valid block of the current blockchain')
@click.pass_obj
def view(ctx):
    port = ctx["port"]
    my_ip = socket.gethostbyname(socket.gethostname())
    #url = "http://" + 'localhost'+ ":" + str(port) + '/cli_view'
    url = "http://" + str(my_ip) + ":" + str(port) + '/cli_view'
    req = requests.get(url)
    click.echo(req.text)

@click.command(name = 'balance', help = 'Show the balance of the current node`s wallet')
@click.pass_obj
def balance(ctx):
    port = ctx["port"]
    my_ip = socket.gethostbyname(socket.gethostname())
    #url = "http://" + 'localhost'+ ":" + str(port) +'/cli_balance'
    url = "http://" + str(my_ip) + ":" + str(port) + '/cli_balance'
    req = requests.get(url)
    click.echo(req.text)

cli.add_command(balance)
cli.add_command(view)
cli.add_command(t)

if __name__ == '__main__':
    cli()
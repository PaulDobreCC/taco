import click
import requests
from clickclick import AliasedGroup, Action, choice, FloatRange, OutputFormat, __version__, get_now
from clickclick import ok, warning, error, fatal_error, action, info
from clickclick.console import print_table
import time
import json as _json
from prettytable import PrettyTable
from sty import fg, bg, ef, rs

STYLES = {
	'SUCCESS': {'fg': 'green'},
	'ERROR': {'fg': 'red'},
	'WARNING': {'fg': 'yellow', 'bold': True},
	'PRICE_UP': {'fg': 'green', 'background': 'black'},
	'PRICE_DOWN': {'fg': 'red', 'background': 'black'},
}

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('I was invoked without subcommand')


def verbose_request_start(value):
	click.secho(' *', fg='green', nl=False)
	click.secho(' ' + 'Requesting endpoint', fg='white', nl=False)
	click.secho(' ' + value + ' ', fg='blue', bold=True)

def verbose_status_code(value, elapsed):
	if value == 200:
		bg_status_code = bg(29,139,58)
		fg_elapsed = 'green'
	else:
		bg_status_code = bg.red
		fg_elapsed = 'red'

	click.secho(' * ', fg='green', nl=False)
	click.secho(bg_status_code + fg.white + ' ' + str(value) + ' ' + rs.all, bold = True, nl=False)
	click.secho(' ' + 'Request status ' + ' ', fg='white', nl=False)
	click.secho('- ' + str(elapsed) + '', fg=fg_elapsed)
	#click.echo('\n')

@cli.command('stripped')
@click.pass_context
@click.option('--fsyms', default='BTC', help='FSYMS parameter')
@click.option('--tsyms', default='USD', help='TSYMS parameter')
@click.option('--json', is_flag=True)
@click.option('--verbose', is_flag=True)
def stripped(ctx, fsyms, tsyms, json, verbose):
	TITLES = {
	    'pair': 'Pair',
	    'price': 'Price',
	}

	MAX_COLUMN_WIDTHS = {
	    'pair': 30,
	    'price': 50,
	}

	url = 'https://min-api.cryptocompare.com/data/pricemulti'

	if verbose == True and json == False:
		verbose_request_start(url)

	payload = {'fsyms': fsyms, 'tsyms': tsyms}
	try:
		r = requests.get(url, params=payload, stream=True)
		r.raise_for_status()
		if verbose == True and json == False:
			verbose_status_code(r.status_code, r.elapsed.total_seconds())
	except requests.exceptions.HTTPError as e:
		verbose_status_code(r.status_code, r.elapsed.total_seconds())
		return -1
	except requests.exceptions.RequestException as e:
		#print('Connection error: {}'.format(e))
		if verbose == True and json == False:
			verbose_status_code(r.status_code, 0)
			return -1

	if json == True:
		click.echo(r.json())
	else:
		for sym, sobj in r.json().items():
			click.secho('     ' + sym + '      ', bg='black', fg='blue')
			rows = []
			for key,value in sobj.items():
				pair = sym + '-' + key
				rows.append({'pair': pair, 'price': str(value)})

			print_table('pair price'.split(), rows,
			                styles=STYLES, titles=TITLES, max_column_widths=MAX_COLUMN_WIDTHS)


@cli.command('price')
@click.pass_context
@click.option('--fsyms', default='BTC', help='FSYMS parameter')
@click.option('--tsyms', default='USD', help='TSYMS parameter')
@click.option('--extra', is_flag=True)
@click.option('--json', is_flag=True)
@click.option('--verbose', is_flag=True)
def price(ctx, fsyms, tsyms, json, verbose, extra):
	TITLES = {
	    'label': 'Label',
	    'value': 'Value',
	}

	BANNED_COLUMNS = ['FROMSYMBOL', 'TOSYMBOL', 'LASTTRADEID', 'PRICE']

	MAX_COLUMN_WIDTHS = {
	    'pair': 30,
	    'price': 50,
	}

	url = 'https://min-api.cryptocompare.com/data/pricemultifull'

	if verbose == True and json == False:
		verbose_request_start(url)

	payload = {'fsyms': fsyms, 'tsyms': tsyms}
	try:
		r = requests.get(url, params=payload, stream=True)
		r.raise_for_status()
		if verbose == True and json == False:
			verbose_status_code(500, r.elapsed.total_seconds())
	except requests.exceptions.HTTPError as e:
		verbose_status_code(400, r.elapsed.total_seconds())
		return -1
	except requests.exceptions.RequestException as e:
		#print('Connection error: {}'.format(e))
		if json == False:
			verbose_status_code(500, 0)
		return -1


	if json == True:
		click.echo(r.json())
	else:
		table = PrettyTable(['Pair', 'Price', 'Percentage'])
		table.align = 'r'
		for ckey, cvalue in r.json()['DISPLAY'].items():
			rows = []
			for key,value in cvalue.items():
				col_pair = '' + ckey + '-' + key + ' '
				if float(value['CHANGEPCT24HOUR']) > 0:
					col_price = fg(29,139,58) + ' ' + str(value['PRICE']) + rs.all
					col_percentage = fg.white + bg(29,139,58) + '+'+ str(value['CHANGEPCT24HOUR']) + '% ' + ' ▲ '  + rs.all
				if float(value['CHANGEPCT24HOUR']) < 0:
					col_price = fg.red + ' ' + str(value['PRICE']) + rs.all
					col_percentage = fg.white + bg.red + str(value['CHANGEPCT24HOUR']) + '% ' + ' ▼ '  + rs.all
				if float(value['CHANGEPCT24HOUR']) == 0:
					col_price = fg.red + ' ' + str(value['PRICE']) + rs.all
					col_percentage = fg.white + bg.blue + str(value['CHANGEPCT24HOUR']) + '% ' + ' ◎ '  + rs.all	
				
				table.add_row([col_pair, col_price, col_percentage])

			if extra == True:
				click.secho(table.get_string())
				table.clear_rows()
				for ikey, ivalue in value.items():
					if ikey not in BANNED_COLUMNS:
						rows.append({'label': ikey, 'value': ivalue})
				print_table('label value'.split(), rows,
					       styles=STYLES, titles=TITLES, max_column_widths=MAX_COLUMN_WIDTHS)
				rows = []
				#pair = sym + '-' + key
			#rows.append({'pair': pair, 'price': str(value)})
		if extra == False:
			click.secho(table.get_string())



if __name__ == '__main__':
    cli()

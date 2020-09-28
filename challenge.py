import argparse
import pyRofex
import os
from dotenv import load_dotenv

load_dotenv()
ORDER_FIXED_AMOUNT = os.getenv('ORDER_FIXED_AMOUNT')

instruments = []

# Inicializar el parser
parser = argparse.ArgumentParser()
# Argumentos largos y cortos
parser.add_argument("simbolo")
parser.add_argument("--usuario", "-u", help="usuario")
parser.add_argument("--password", "-p", help="contraseña")
parser.add_argument("--cuenta", "-c", help="cuenta")
# Leer los argumentos de la línea de comando
args = parser.parse_args()

if args.simbolo:
    instruments.append(args.simbolo)
if args.usuario:
    REMARKETS_USER = args.usuario
if args.password:
    REMARKETS_PASSWORD = args.password
if args.cuenta:
    REMARKETS_ACCOUNT = args.cuenta


#Intentar conexión con credenciales proporcionadas
try:
    pyRofex.initialize(user=REMARKETS_USER,
                password=REMARKETS_PASSWORD,
                account=REMARKETS_ACCOUNT,
                environment=pyRofex.Environment.REMARKET)
except:
    print("Error: revisa tu usuario, contraseña y cuenta")


#MD último precio
def hasLastPrice(md):
    if md['marketData']['LA']:
        return md['marketData']['LA']['price']
    else:
        return None

#MD bids
def hasBids(md):
    if md['marketData']['BI'] != [] and md['marketData']['BI'] != None:
        precioBid = md['marketData']["BI"][0]["price"]
        return precioBid
    else:
        return None

#MD Efectuar bid en base a si había bids activas
def performBid(md):
    simbolo = md['instrumentId']['symbol']
    if hasBids(md): 
        bidAmount = hasBids(md) - 0.01
    else:
        bidAmount = ORDER_FIXED_AMOUNT
    order = pyRofex.send_order(ticker=simbolo,
                           side=pyRofex.Side.BUY,
                           size=1,
                           price=bidAmount,
                           order_type=pyRofex.OrderType.LIMIT)
    orderStatus = pyRofex.get_order_status(order["order"]["clientId"])
    if orderStatus['status'] == 'OK':
        return orderStatus
    else:
        return False


#Handlers
def market_data_handler(message):
    # print("Market Data Message Received: {0}".format(message))
    print("Consultando símbolo")
    performOperation(message)
    print("Cerrando sesión en Remarkets")
    pyRofex.close_websocket_connection()

def order_report_handler(message):
    print("Order Report Message Received: {0}".format(message))

def error_handler(message):
    # print("Error Message Received: {0}".format(message))
    if message['status'] == 'ERROR' and "don't exist" in message['description']:
        print("Símbolo Inválido")
        print("Cerrando sesión en Remarkets")
        pyRofex.close_websocket_connection()

def exception_handler(e):
    print("Exception Occurred: {0}".format(e.message))


# Inicializar conexión websocket
try:
    pyRofex.init_websocket_connection(market_data_handler=market_data_handler,
                                    order_report_handler=order_report_handler,
                                    error_handler=error_handler,
                                    exception_handler=exception_handler)
    
    print("Iniciando sesión en Remarkets")

    entries = [pyRofex.MarketDataEntry.BIDS,
            pyRofex.MarketDataEntry.LAST]

    pyRofex.market_data_subscription(tickers=instruments,
                                    entries=entries)
except:
    print("La sesión no se ha iniciado")


def performOperation(md):
    lastPrice = hasLastPrice(md)
    if lastPrice:
        print(f"Último precio operado: ${lastPrice}")
    else:
        print(f"Último precio operado: Desconocido")
    print("Consultando BID")
    bids = hasBids(md)
    if bids:
        print(f"Precio de BID ${bids}")
    else:
        print("No hay bids activos")
    orderStatus = performBid(md)
    if (orderStatus['order']['status']) == 'REJECTED':
        print(f"La orden ha sido rechazada, razón:{orderStatus['order']['text']}")
    elif orderStatus['status'] == 'OK':
        print(f"Ingresando orden a ${orderStatus['order']['price']}")

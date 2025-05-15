import os
import requests
import time
from datetime import datetime
import pytz
from dhanhq import dhanhq

ACCESS_TOKEN = os.environ['token']
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
client_id = os.environ['client_id']

BOT_TOKEN2 = os.environ['BOT_TOKEN2']
CHAT_ID2 = os.environ['CHAT_ID2']

BASE_URL = 'https://api.dhan.co'
HEADERS = {
    'access-token': ACCESS_TOKEN,
    'Content-Type': 'application/json'
}


dhan = dhanhq(client_id , ACCESS_TOKEN)  # Replace with your actual access token


total_sellQTY = 0 
count = 1



ist = pytz.timezone('Asia/Kolkata')
today = datetime.now(ist).date()

# Track last deactivation date
last_deactivated_date = None
last_profit_day = None
last_notification = None
last_sent_hour = -1

def is_after_8am_ist():
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    return now_ist.hour >= 8

def is_after_4pm_ist():
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    return now_ist.hour >= 16


def is_trading_day():
    now = datetime.now()
    weekday = now.weekday()
    # 0 = Monday, ..., 6 = Sunday
    return weekday < 5  # True for Monday to Friday




def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print("")
    else:
        print("Failed to send message:", r.text)

def health_chech_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN2}/sendMessage"
    payload = {
        'chat_id': CHAT_ID2,
        'text': message
    }
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print("")
    else:
        print("Failed to send message:", r.text)


def enable_kill_switch():
    """ Enables kill switch """
    #https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE
    url = f"{BASE_URL}/settings/kill-switch"
    response = requests.post('https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE', headers=HEADERS)
    if response.status_code == 200:
        print(" Kill switch ENABLED.")
    else:
        send_telegram_message(" Failed to enable kill switch:", response.text)

def disable_kill_switch():
    """ Disables kill switch """
    url = f"{BASE_URL}/killSwitch?killSwitchStatus=DEACTIVATE"
    response = requests.post(url, headers=HEADERS)
    if response.status_code == 200:
        print(" Kill switch DISABLED.")
    else:
        send_telegram_message(" Failed to disable kill switch:", response.text)




def get_daily_pnl():
    url = f"{BASE_URL}/positions"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        positions = response.json()
        total_realized_pnl = 0
        total_unrealized_pnl = 0

        for pos in positions:
            #print(pos)
            # Realized P&L: from closed positions
            realized = float(pos.get('realizedProfit', 0))
            # Unrealized P&L: from open positions
            unrealized = float(pos.get('unrealizedProfit', 0))

            total_realized_pnl += realized
            total_unrealized_pnl += unrealized

        total_pnl = total_realized_pnl + total_unrealized_pnl
        #print(total_realized_pnl , total_unrealized_pnl)
        # print(f"Realized P&L: ₹{total_realized_pnl}")
        # print(f"Unrealized P&L: ₹{total_unrealized_pnl}")
        # print(f"Total P&L for today: ₹{total_pnl}")
        return total_pnl
    else:
        print(f"Error fetching positions: {response.status_code} - {response.text}")
        return None




def get_today_trade_count():
    global total_sellQTY
    total_sellQTY = 0
    total_trade = 0

    try:
        orders = dhan.get_order_list()
        if(orders.get('status' == 'failure')):
            return 'failed'
            #send_telegram_message("Error in featching pending oredr list")
        if(not orders.get('data')):
            print("No Pending Orders")
        # print(len(orders.get('data')))
        # print(orders)
        for order in orders.get('data'):
            #print(order['orderStatus'])
            if order.get("orderStatus") == 'TRADED':
                if order.get('transactionType') == 'SELL':
                    total_sellQTY += order.get('quantity')
                total_trade += 1
        return total_trade

    except Exception:
         print(f"Error fetching trade Count")


#print(get_today_trade_count())

    # url = f"{BASE_URL}/trades"
    # response = requests.get(url, headers=HEADERS)
    # if response.status_code == 200:
    #     trades = response.json()
    #     for trade in trades:
    #         if(trade["transactionType"] == 'SELL'):
    #             total_sellQTY += trade["tradedQuantity"]
    
    
    #     trade_count = len(trades)
        
    #     return trade_count
    # else:
    #     print(f"Error fetching trade book: {response.status_code} - {response.text}")
    #     return 0



#######################################################################################



def get_positions():
    url = f"{BASE_URL}/positions"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching positions:", response.text)
        send_telegram_message("Error fetching positions:", response.text)
        return 'failed'

def place_order(order_data):
    url = f"{BASE_URL}/orders"
    response = requests.post(url, json=order_data, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error placing order:", response.text)
        send_telegram_message("Error placing order:", response.text)
        return 'failed'

def close_all_positions():
    positions = get_positions()
    if positions == 'failed':
        return 'failed'
    #print("nabd")
    if not positions:
        print("No open positions.")
        return

    for pos in positions:
        #print(pos)
        net_qty = int(pos.get("netQty", 0))
        print("Positions are already closed")
        if net_qty != 0:
            security_id = pos["securityId"]
            trading_symbol = pos["tradingSymbol"]
            product_type = pos["productType"]
            exchange_segment = pos["exchangeSegment"]

            print(f"Closing position for: {trading_symbol}, Qty: {net_qty}")

            # Place opposite order to square off
            order_data = {
                "transactionType": "SELL" if net_qty > 0 else "BUY",
                "securityId": security_id,
                "quantity": abs(net_qty),
                "orderType": "MARKET",
                "productType": product_type,
                "exchangeSegment": exchange_segment,
                "orderValidity": "DAY",
                "price": 0,
                "tag": "AutoClose"
            }

            response = place_order(order_data)
            if response == 'failed':
                return 'failed'
            print(f"Square-off response: {response}")
            time.sleep(1)  # avoid rate limits


def cancel_pending_orders():
    # Fetch all orders
    try:
        orders = dhan.get_order_list()
        if(orders.get('status' == 'failure')):
            return 'failed'
            #send_telegram_message("Error in featching pending oredr list")
        if(not orders.get('data')):
            print("No Pending Orders")

        for order in orders.get('data'):
            print(order['orderStatus'])
            if order.get("orderStatus") == "PENDING":
                order_id = order.get("orderId")
                print(f"Cancelling order: {order_id}")
                response = dhan.cancel_order(order_id)
                if(response.get('status') ==  'failure'):
                    return 'failed'
                    #send_telegram_message("Error In Closing the pending orders")
                print(f"Response: {response}")
        
    except Exception:
        return 'failed'


def health_check():
    global last_sent_hour
    current_hour = datetime.now(ist).hour

    if current_hour != last_sent_hour:
        health_chech_message("🕐 Chal rha hu bhai \n . \n . \n")
        last_sent_hour = current_hour




flag = 1


while True:

    health_check()
    today = datetime.now(ist).date()

    

    if not is_trading_day():
        if(last_notification != today and is_after_8am_ist()):
            print("Not a trading day ENJOY")
            last_notification = today
        send_telegram_message("Not a trading day ENJOY")
        time.sleep(3600)
        continue

    print("***************************************************************************")
    
    time.sleep(10)
    c = get_today_trade_count()
    p = get_daily_pnl()


    if(last_notification != today and is_after_4pm_ist):
        send_telegram_message(f"\n\nTrade Summary: \n Total PNL: {p} \n Total trade: {c} \n Total QTY: {total_sellQTY} \n\n")
        last_notification = today

    if(p >= 3000 and last_profit_day != today):
        send_telegram_message("⚠️ Good Job:  ₹3️⃣0️⃣0️⃣0️⃣ Profit. ")
        last_profit_day = today
        

    if(p <= -3000 and flag == 1):
        send_telegram_message("⚠️ Loss Alert: ₹3️⃣0️⃣0️⃣0️⃣ loss hit. Consider reviewing your trades.")
        flag = 0
    if(flag == 0 and p > 0):
        send_telegram_message("⚠️ Profit Alert: You are in Green from RED. Consider reviewing your trades.")
        flag = 1

    print("Total trades executed today:" , c)
    print("Today PNL:" , p )
    print("Total Quantity Traded:" , total_sellQTY)
    if(is_after_8am_ist() and last_deactivated_date != today):
        print("Eligible for deactivation")
        if(total_sellQTY >= 300 or p < -3900):
            print("All Coditions are True for diactivation")
            if(count ==2):
                
                #print("Activated")
                r = cancel_pending_orders()
                if(r == 'failed'):
                    send_telegram_message("Error in cancelling the Pending orders")
                    continue
                time.sleep(10)
                r2 = close_all_positions()
                if(r2 == 'failed'):
                    send_telegram_message("Error in closing the open positions")
                    continue
                time.sleep(10)
                enable_kill_switch()
                disable_kill_switch()
                enable_kill_switch()
                count = 1
                last_deactivated_date = today
                send_telegram_message("Kill Switch activated for the day \n 𝓔𝓷𝓳𝓸𝔂 𝓣𝓱𝓮 𝓓𝓪𝔂")

                
                
                
                
            else:
                count += 1
        else:
            print("Loss limit OR quantity not crossed")
    else:
        print("Kill Switch activated for the day")
        
















# import json

# ACCESS_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzQ5NjQ5OTkyLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMzg0MjUxMiJ9.LCLcfpnfLCGe_SKat1HgoX03_hwRAqXTR8PWY2-etBofqYBoksIIKxyRDQMiJVXD480BsxAKRunGzh3OoHf75Q'  # Replace with your actual access token
# BASE_URL = 'https://api.dhan.co'
# HEADERS = {
#     'access-token': ACCESS_TOKEN,
#     'Content-Type': 'application/json'
# }

# def get_today_trade_count():
#     url = f"{BASE_URL}/trades"
#     response = requests.get(url, headers=HEADERS)
#     if response.status_code == 200:
#         trades = response.json()
#         print(json.dumps(trades))
#         trade_count = len(trades)
#         print(f"Total trades executed today: {trade_count}")
#         return trade_count
#     else:
#         print(f"Error fetching trade book: {response.status_code} - {response.text}")
#         return 0

# # Example usage
# get_today_trade_count()

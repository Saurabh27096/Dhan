import requests
import json

ACCESS_TOKEN = os.environ['token']
BASE_URL = 'https://api.dhan.co'
HEADERS = {
    'access-token': ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

total_sellQTY = 0 




def enable_kill_switch():
    """ Enables kill switch """
    #https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE
    url = f"{BASE_URL}/settings/kill-switch"
    response = requests.post('https://api.dhan.co/killSwitch?killSwitchStatus=ACTIVATE', headers=HEADERS)
    if response.status_code == 200:
        print(" Kill switch ENABLED.")
    else:
        print(" Failed to enable kill switch:", response.text)

def disable_kill_switch():
    """ Disables kill switch """
    url = f"{BASE_URL}/killSwitch?killSwitchStatus=DEACTIVATE"
    response = requests.post(url, headers=HEADERS)
    if response.status_code == 200:
        print(" Kill switch DISABLED.")
    else:
        print(" Failed to disable kill switch:", response.text)




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
    url = f"{BASE_URL}/trades"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        trades = response.json()
        for trade in trades:
            if(trade["transactionType"] == 'SELL'):
                total_sellQTY += trade["tradedQuantity"]
    
    if(total_sellQTY == 300):
        #print("DONE")
        enable_kill_switch()
        



        #print(json.dumps(trades))
        trade_count = len(trades)
        print(f"Total trades executed today: {trade_count}")
        return trade_count
    else:
        print(f"Error fetching trade book: {response.status_code} - {response.text}")
        return 0


while True:
    c = get_today_trade_count()
    p = get_daily_pnl()
    print("Today PNL:" , p )
    if(total_sellQTY == 300 or p < 3900):
        enable_kill_switch()
        disable_kill_switch()
        enable_kill_switch()
        break
















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

import MetaTrader5 as mt5
from pyrogram import Client, filters
import re

# Initialize the MetaTrader 5 client
mt5.initialize()

# Login to the MetaTrader 5 account
login_result = mt5.login(login=328913912, server="MetaQuotes-Demo", password="4378213312") # this is just example of login detail 

if login_result:
    print("Login successful")
else:
    print("Login failed:", mt5.last_error())

# Dictionary to map channels to trading details
channels = {
    -1002053376750: {'type': 'channel', 'trading': 'str_long', 'url': '@test_forward1234'},
}

# List of trading symbols
symbols = ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'CHFJPY', 'GBPAUD', 'GBPCAD',
           'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD',
           'EURUSD', 'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDCNH', 'USDJPY', 'XAUUSD']


# Function to extract trade details like action, symbol, price, SL, and TP levels
def extract_trade_details(text):
    try:
        text = text.upper()
        # Extracting the action, symbol, price, SL, and TP values using regular expressions
        action_symbol_match = re.findall(r'(BUY|SELL)\s+(\S+)', text)
        if action_symbol_match:
            action, symbol = action_symbol_match[0]
        else:
            raise ValueError("Action and symbol not found in text")

        price_match = re.findall(r'[\d.]+', text)
        if price_match:
            price = float(price_match[0])
        else:
            raise ValueError("Price not found in text")

        tp_matches = re.findall(r'TP\d\s+([\d.]+)', text)  # Extract all TP values
        if len(tp_matches) >= 3:
            TP1, TP2, TP3 = map(float, tp_matches[:3])
        else:
            raise ValueError("Insufficient Take Profit (TP) values provided")

        sl_match = re.findall(r'SL\s+([\d.]+)', text)
        if sl_match:
            SL = float(sl_match[0])
        else:
            raise ValueError("Stop Loss (SL) not found in text")

        return action, symbol, price, TP1, TP2, TP3, SL

    except Exception as ex:
        print("Exception in extract_trade_details:", ex)
        return None

# Function to send trading order
def send_trading_order(symbol, lot, action, price, SL, TP1, TP2, TP3):
    try:

        type = mt5.ORDER_TYPE_BUY_LIMIT if action == 'BUY' else mt5.ORDER_TYPE_SELL_LIMIT

        # Validate stop loss and take profit values
        if SL <= 0 or TP1 <= 0 or TP2 <= 0 or TP3 <= 0:
            print("Invalid stop loss or take profit value.")
            return False

        # Validate price
        if price <= 0:
            print("Invalid price value.")
            return False
    
        # Get current symbol information
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info.visible:
            print("Symbol not found or not visible.")
            return False

        # Check if current price falls within specific ranges of TP values based on action
        if action == 'BUY':
            print("nigga", price)
            if TP1 < price < TP2:
                # Adjust price to current market price
                symbol_info = mt5.symbol_info_tick(symbol)
                if symbol_info:
                    current_price = symbol_info.ask
                    print("Adjusting price to current market price:", current_price)
                    tp_values = [TP2, TP3]

                else:
                    print("Failed to get current market price.")
                    return False
            elif TP1 < TP2 and TP2 < price < TP3:
                # Adjust price to current market price
                symbol_info = mt5.symbol_info_tick(symbol)
                if symbol_info:
                    current_price = symbol_info.ask
                    print("Adjusting price to current market price:", current_price)
                    tp_values = [TP3]
                    
                else:
                    print("Failed to get current market price.")
                    return False
            elif price < TP1:
                symbol_info = mt5.symbol_info_tick(symbol)
                if symbol_info:
                    #current_price = text.sym
                    print("Price is above TP1. Executing order without adjustment.")
                    tp_values = [TP1, TP2, TP3]
                else:
                    print("Current price is lower than all TP values.")
                    return False

        elif action == 'SELL':
            if TP1 > price > TP2:
                # Adjust price to current market price
                symbol_info = mt5.symbol_info_tick(symbol)
                if symbol_info:
                    current_price = symbol_info.bid
                    print("Adjusting price to current market price:", current_price)
                    tp_values = [TP2, TP3]
                else:
                    print("Failed to get current market price.")
                    return False
            elif TP1 > TP2 and TP2 > price > TP3:
                # Adjust price to current market price
                symbol_info = mt5.symbol_info_tick(symbol)
                if symbol_info:
                    current_price = symbol_info.bid
                    print("Adjusting price to current market price:", current_price)
                    tp_values = [TP3]
                else:
                    print("Failed to get current market price.")
                    return False
            elif price > TP1:
                symbol_info = mt5.symbol_info_tick(symbol)
                if symbol_info:
                    #current_price = text.sym
                    print("Price is above TP1. Executing order without adjustment.")
                    tp_values = [TP1, TP2, TP3]
                else:
                    print("Current price is lower than all TP values.")
                    return False
        
        for tp in tp_values:
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": lot,
                "type": type,
                "price": price,
                "sl": SL,
                "tp": tp,
                "deviation": 3,
                "magic": 99999,  # Fixed magic number
                "comment": "Limit Order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,  # Specify the type of order filling
            }
            result = mt5.order_send(request)
            if result == -1:
                print(f"OrderSend failed: {str(mt5.last_error())}")
                return False
            else:
                print("Limit order placed successfully.")

        return True
    except Exception as ex:
        print(f"OrderSend failed: {ex}")
        return False

# Initialize Pyrogram client
bot = Client("forwarder", api_id="54572384", api_hash="218398df9asa9792381dsada09092dsa") #this is example of your bot api_id and api_hash ( you can get this by create bot on telegram application )

# Define the message handler function
@bot.on_message(filters.channel)
def handle_message(client, message):
    print("Message received:", message.text)  # Debugging statement
    chat_id = message.chat.id
    text = str(message.text).lower()
    if message.photo:
        if message.caption:
            text = message.caption
    if chat_id in channels:
        print("Chat ID found in channels.")  # Debugging statement
        if any(symbol.lower() in text for symbol in symbols):
            print("Symbol found in message.")  # Debugging statement
            if 'buy' in text or 'sell' in text:
                print("Buy or sell action found.")  # Debugging statement
                trade_details = extract_trade_details(text)
                print("Trade details:", trade_details)  # Debugging statement
                if trade_details:
                    action, symbol, price, tp1, tp2, tp3, sl = trade_details
                    symbol = symbol.upper()
                    print("Symbol:", symbol)  # Debugging statement
                    lot = 0.01
                    magic = 99999  # Fixed magic number
                    type = mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL
                    symbol_info = mt5.symbol_info_tick(symbol)
                    print("Symbol info:", symbol_info)  # Debugging statement
                    if symbol_info:
                        current_price = symbol_info.ask if type == mt5.ORDER_TYPE_BUY else symbol_info.bid
                        print("Current price:", current_price)  # Debugging statement
                        if current_price:
                            if send_trading_order(symbol, 0.01, action, current_price, sl, tp1, tp2, tp3):
                                print("Order placed successfully.")
                                # Send a message back to the client
                                bot.send_message(chat_id, "Order placed successfully.")
                            else:
                                print("Failed to place order.")
                                # Send a message back to the client
                                bot.send_message(chat_id, "Failed to place order.")
                        else:
                            print(f"Failed to get current price for symbol: {symbol}")
                            # Send a message back to the client
                            bot.send_message(chat_id, f"Failed to get current price for symbol: {symbol}")
                    else:
                        print(f"Failed to get symbol info for symbol: {symbol}")
                        # Send a message back to the client
                        bot.send_message(chat_id, f"Failed to get symbol info for symbol: {symbol}")
                else:
                    print("Failed to extract trade details from message.")
                    # Send a message back to the client
                    bot.send_message(chat_id, "Failed to extract trade details from message.")
            else:
                print("No buy or sell action found.")  # Debugging statement
        else:
            print("Symbol not found in message.")  # Debugging statement
    else:
        print("Chat ID not found in channels.")  # Debugging statement

# Run the Pyrogram client
if __name__ == "__main__":
    bot.run()

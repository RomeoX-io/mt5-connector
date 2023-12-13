import MetaTrader5 as mt5
mt5.initialize()
login = 42404690
password = '7qXbo^x1&1OS67'
server = 'AdmiralMarkets-Demo'
mt5.login(login, password, server)

def calculate_order_price(symbol, order_type, aggressiveness_score):
    # Ensure MT5 is initialized
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return None

    # Retrieve bid and ask prices
    symbol_info = mt5.symbol_info_tick(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found")
        return None

    # Calculate double the spread
    spread = symbol_info.ask - symbol_info.bid
    double_spread = 2 * spread

    if order_type.lower() == 'buy':
        # For a buy order, add double spread and aggressiveness score to bid
        order_price = symbol_info.bid + double_spread + aggressiveness_score
    elif order_type.lower() == 'sell':
        # For a sell order, subtract double spread and aggressiveness score from ask
        order_price = symbol_info.ask - double_spread - aggressiveness_score
    else:
        print("Invalid order type. Please use 'buy' or 'sell'")
        return None

    return order_price

# Example usage
symbol = "EURUSD"
order_type = "buy"
aggressiveness_score = 0.0001  # Example value, adjust as needed
order_price = calculate_order_price(symbol, order_type, aggressiveness_score)
if order_price is not None:
    print(f"Calculated order price for {order_type} {symbol}: {order_price}")
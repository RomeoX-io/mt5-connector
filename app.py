

import MetaTrader5 as mt5
from db import AssetManager
import asyncio
 
def open_long(symbol, volume, side):
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"Symbol {symbol} not found on the server.")
            return

        if side:
            price = mt5.symbol_info_tick(symbol).bid
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = mt5.symbol_info_tick(symbol).ask
            order_type = mt5.ORDER_TYPE_SELL

        # Adjust the volume to the nearest acceptable lot size if necessary
        min_volume = symbol_info.volume_min
        max_volume = symbol_info.volume_max
        step_volume = symbol_info.volume_step
        volume = max(min_volume, min(volume, max_volume))
        volume = ((int(volume / step_volume)) * step_volume)

        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': order_type,
            'price': price,
            'type_time': mt5.ORDER_TIME_GTC,
        }

        print(f"Sending trade request for {symbol}: {request}")
        result = mt5.order_send(request)

        if result is not None and result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to open position for {symbol}. Error code: {result.retcode}, Comment: {result.comment}")
        elif result is not None:
            print(f"Opened position for {symbol}: {result.comment}")
        else:
            print(f"Failed to open position for {symbol}. The order_send function returned None.")
    except Exception as e:
        print(f"Exception while sending order for {symbol}: {e}")




def update_open_positions(manager):
    for symbol in manager.get_assets().keys():
        update_open_position(manager, symbol)

def update_open_position(manager, symbol):
    try:
        positions = mt5.positions_get(symbol=symbol)
        if positions is not None:  # This should be 'is not None' to make sure positions exist
            # Calculate the net quantity
            net_qty = get_current_position_size(symbol)
            manager.update_open(symbol, net_qty)
        else:
            manager.update_open(symbol, 0)  # If positions is None, set open to 0
    except Exception as e:
        print(f"Error updating position for {symbol}: {e}")


def manage_inventory(manager):
    update_open_positions(manager)
    targets = manager.get_assets_to_update()
    print(f"Targets to update: {targets}")

    for symbol, target_qty in targets.items():
        net_current_qty = abs(get_current_position_size(symbol))

        if target_qty >= 0:
            target_qty = abs(target_qty)
            closed_amount = close_positions(symbol, min(target_qty,net_current_qty), is_short=True)
            qty_to_open = target_qty - abs(closed_amount)
            print(f"Opening {qty_to_open} long positions for {symbol}")
            open_long(symbol, qty_to_open, True)

        elif target_qty < 0:
            target_qty = abs(target_qty)
            closed_amount = close_positions(symbol, min(target_qty,net_current_qty), is_short=True)
            qty_to_open = target_qty - abs(closed_amount)
            print(f"Opening {qty_to_open} short positions for {symbol}")
            open_long(symbol, qty_to_open, False)




def has_opposite_positions(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return False

    longs = shorts = False
    for position in positions:
        if position.type == mt5.ORDER_TYPE_BUY:
            longs = True
        elif position.type == mt5.ORDER_TYPE_SELL:
            shorts = True

    return longs and shorts


def get_current_position_size(symbol):
    total_qty = 0
    positions = mt5.positions_get(symbol=symbol)
    if positions is not None:  # Ensure that positions were retrieved
        for position in positions:
            # Add or subtract the volume depending on the type (buy or sell)
            if position.type == mt5.ORDER_TYPE_BUY:
                total_qty += position.volume
            elif position.type == mt5.ORDER_TYPE_SELL:
                total_qty -= position.volume
    return total_qty



def close_positions(symbol, amount_to_close, is_short):
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        mt5.shutdown()
        return 0

    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        print(f"No positions to close for {symbol}")
        return 0

    closed_volume = 0
    for position in positions:
        if (is_short and position.type == mt5.ORDER_TYPE_SELL) or \
           (not is_short and position.type == mt5.ORDER_TYPE_BUY):
            volume_to_close = min(amount_to_close - closed_volume, position.volume)
            order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume_to_close,
                "type": order_type,
                "position": position.ticket,
                "price": price,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Error closing position {position.ticket}: {result.retcode}, Request: {request}")
            else:
                print(f"Position {position.ticket} closed successfully")
                closed_volume += volume_to_close

            if closed_volume >= amount_to_close:
                break

    return closed_volume



async def loop():
    while True:
        try:
            manager = AssetManager('assets.json')
            manage_inventory(manager)
        except Exception as e:
            print(f"Error during loop iteration: {e}")
        await asyncio.sleep(3)

if __name__ == '__main__':
    mt5.initialize()
    login = 42404690
    password = '7qXbo^x1&1OS67'
    server = 'AdmiralMarkets-Demo'
    mt5.login(login, password, server)
    #manage_inventory(manager)
    asyncio.run(loop())
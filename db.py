from flask import Flask, request, jsonify
import json
import MetaTrader5 as mt5
mt5.initialize()
login = 42404690
password = '7qXbo^x1&1OS67'
server = 'AdmiralMarkets-Demo'
mt5.login(login, password, server)

app = Flask(__name__)
json_file = 'assets.json'



class AssetManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.assets = self.read_json()

    def read_json(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def write_json(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.assets, file, indent=4)
    

    def add_asset(self, asset_name):
        if asset_name not in self.assets:
            self.assets[asset_name] = {'target': 10, 'open': 0}
            self.write_json()

    def update_target(self, asset_name, target_value):
        if asset_name not in self.assets:
            self.add_asset(asset_name)
        self.assets[asset_name]['target'] = target_value
        self.write_json()

    def update_open(self, asset_name, open_value):
        if asset_name not in self.assets:
            self.add_asset(asset_name)
        self.assets[asset_name]['open'] = open_value
        self.write_json()

    def get_assets(self):
        return self.assets

    def get_assets_to_update(self):
        to_update = {}
        for asset, values in self.assets.items():
            if values['target'] - values['open'] != 0:
                to_update[asset] = values['target'] - values['open']
        return to_update
    
    def get_target_amount(self, asset_name):
        # Retrieve the target amount for the given asset
        if asset_name in self.assets:
            return self.assets[asset_name]['target']
        else:
            # If the asset does not exist, return zero or handle as appropriate
            return 0
manager = AssetManager(json_file)

@app.route('/update_target', methods=['POST'])
def update_target():
    asset_name = request.json.get('asset')
    target_value = request.json.get('target')
    manager.update_target(asset_name, target_value)
    return jsonify({"message": "Target updated."}), 200

@app.route('/get_assets', methods=['GET'])
def get_assets():
    return jsonify(manager.get_assets())


@app.route('/account_info')
def account_info():
    account_info = mt5.account_info()
    if account_info is None:
        return jsonify({'error': 'Could not retrieve account information'}), 500
    balance = account_info.equity
    upnl = account_info.margin_free
    return jsonify({'balance': balance, 'upnl': upnl})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
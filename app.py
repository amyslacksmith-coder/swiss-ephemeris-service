from flask import Flask, request, jsonify
import swisseph as swe
import os

app = Flask(__name__)
swe.set_ephe_path(None)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Swiss Ephemeris API is running", "version": "1.0"})

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    year, month, day = map(int, data['birthDate'].split('-'))
    hour, minute = map(int, data['time'].split(':'))
    
    jd = swe.julday(year, month, day, hour + minute/60.0)
    result = swe.calc_ut(jd, swe.TRUE_NODE)
    
    return jsonify({'trueNode': result[0][0]})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
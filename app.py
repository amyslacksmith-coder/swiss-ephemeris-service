from flask import Flask, request, jsonify
import swisseph as swe
import os
from datetime import datetime

app = Flask(__name__)
swe.set_ephe_path(None)

# Planet constants
PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mercury': swe.MERCURY,
    'Venus': swe.VENUS,
    'Mars': swe.MARS,
    'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN,
    'Uranus': swe.URANUS,
    'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO,
    'North Node': swe.TRUE_NODE,
    'Chiron': swe.CHIRON
}

def normalize_degree(deg):
    """Normalize degree to 0-360 range"""
    deg = deg % 360
    if deg < 0:
        deg += 360
    return deg

def get_zodiac_sign(degree):
    """Get zodiac sign from degree"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    return signs[int(normalize_degree(degree) / 30)]

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "Swiss Ephemeris API is running",
        "version": "2.0",
        "endpoints": {
            "/calculate": "POST - Calculate all planets",
            "/": "GET - This status page"
        }
    })

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        
        # Parse input
        birth_date = data['birthDate']
        birth_time = data['time']
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        
        year, month, day = map(int, birth_date.split('-'))
        hour, minute = map(int, birth_time.split(':'))
        
        # Calculate Julian Day (UT)
        time_decimal = hour + minute / 60.0
        jd = swe.julday(year, month, day, time_decimal)
        
        # Calculate all planets
        planets = []
        
        for name, planet_id in PLANETS.items():
            result = swe.calc_ut(jd, planet_id)
            
            longitude_deg = result[0][0]
            latitude_deg = result[0][1]
            distance = result[0][2]
            speed = result[0][3]
            
            planets.append({
                'name': name,
                'fullDegree': normalize_degree(longitude_deg),
                'normDegree': normalize_degree(longitude_deg) % 30,
                'sign': get_zodiac_sign(longitude_deg),
                'latitude': latitude_deg,
                'distance': distance,
                'speed': speed,
                'isRetro': 'true' if speed < 0 else 'false'
            })
        
        # Add South Node (180° from North Node)
        north_node = next(p for p in planets if p['name'] == 'North Node')
        south_node_deg = normalize_degree(north_node['fullDegree'] + 180)
        
        planets.append({
            'name': 'South Node',
            'fullDegree': south_node_deg,
            'normDegree': south_node_deg % 30,
            'sign': get_zodiac_sign(south_node_deg),
            'latitude': -north_node['latitude'],
            'distance': north_node['distance'],
            'speed': north_node['speed'],
            'isRetro': 'true'
        })
        
        return jsonify({
            'birthDate': birth_date,
            'birthTime': birth_time,
            'latitude': latitude,
            'longitude': longitude,
            'julianDay': jd,
            'planets': planets,
            'calculatedAt': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'message': 'Calculation failed',
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
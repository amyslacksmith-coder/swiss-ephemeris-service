from flask import Flask, request, jsonify  
import swisseph as swe  
import os  
from datetime import datetime  
import sys  

app = Flask(__name__)  
swe.set_ephe_path('.')  # Changed to root where seas_18.se1 is

# Force stdout to flush immediately  
sys.stdout.flush()  

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
    'Chiron': swe.CHIRON,  
    'North Node': swe.TRUE_NODE  
}  

def normalize_degree(deg):  
    deg = deg % 360.0  
    if deg < 0:  
        deg += 360.0  
    return deg  

def get_zodiac_sign(degree):  
    signs = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',  
             'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']  
    index = int(normalize_degree(degree) / 30)  
    return signs[index]  

@app.route('/', methods=['GET'])  
def home():  
    return jsonify({  
        "status": "Swiss Ephemeris API is running",  
        "version": "1.0",  
        "endpoints": {  
            "/calculate": "POST - Calculate all planets and houses",  
            "/": "GET - This status page"  
        }  
    })  

@app.route('/calculate', methods=['POST'])  
def calculate():  
    try:  
        data = request.json  
        birth_date = data['birthDate']        # format "YYYY-MM-DD"  
        birth_time = data['time']             # format "HH:MM" (24h)  
        latitude = float(data['latitude'])    # decimal degrees, North=positive, South=negative  
        longitude = float(data['longitude'])  # decimal degrees, East=positive, West=negative  

        year, month, day = map(int, birth_date.split('-'))  
        hour, minute = map(int, birth_time.split(':'))  
        time_decimal = hour + minute/60.0  

        # Julian Day (UT)  
        jd = swe.julday(year, month, day, time_decimal)  

        # Calculate planet positions  
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
                'degreeInSign': normalize_degree(longitude_deg) % 30.0,  
                'sign': get_zodiac_sign(longitude_deg),  
                'latitude': latitude_deg,  
                'distance': distance,  
                'speed': speed,  
                'isRetro': True if speed < 0 else False  
            })  

        # Add South Node  
        north_node = next(p for p in planets if p['name'] == 'North Node')  
        south_node_deg = normalize_degree(north_node['fullDegree'] + 180.0)  
        planets.append({  
            'name': 'South Node',  
            'fullDegree': south_node_deg,  
            'degreeInSign': south_node_deg % 30.0,  
            'sign': get_zodiac_sign(south_node_deg),  
            'latitude': -north_node['latitude'],  
            'distance': north_node['distance'],  
            'speed': north_node['speed'],  
            'isRetro': True  
        })  

        # Calculate houses (Placidus) - Python binding signature
        cusps, ascmc = swe.houses(jd, latitude, longitude)  

        asc_deg = normalize_degree(ascmc[0])  
        mc_deg  = normalize_degree(ascmc[1])  

        houses = {  
            'ascendant': {  
                'degree': asc_deg,  
                'degreeInSign': asc_deg % 30.0,  
                'sign': get_zodiac_sign(asc_deg)  
            },  
            'midheaven': {  
                'degree': mc_deg,  
                'degreeInSign': mc_deg % 30.0,  
                'sign': get_zodiac_sign(mc_deg)  
            },  
            'cusps': []  
        }  

        for i in range(12):  # FIXED: iterate 0-11 instead of 1-12
            cusp_deg = normalize_degree(cusps[i])  
            houses['cusps'].append({  
                'house': i + 1,  # House numbers are 1-12
                'degree': cusp_deg,  
                'degreeInSign': cusp_deg % 30.0,  
                'sign': get_zodiac_sign(cusp_deg)  
            })  

        return jsonify({  
            'birthDate': birth_date,  
            'birthTime': birth_time,  
            'latitude': latitude,  
            'longitude': longitude,  
            'julianDay': jd,  
            'planets': planets,  
            'houses': houses,  
            'calculatedAt': datetime.utcnow().isoformat() + 'Z'  
        })  

    except Exception as e:  
        import traceback  
        app.logger.error(f"MAIN ERROR: {e}")  
        app.logger.error(traceback.format_exc())  
        return jsonify({  
            'error': str(e),  
            'message': 'Calculation failed',  
            'traceback': traceback.format_exc()  
        }), 500  

if __name__ == '__main__':  
    port = int(os.environ.get('PORT', 8080))  
    app.run(host='0.0.0.0', port=port, debug=True)

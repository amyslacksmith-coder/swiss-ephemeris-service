from flask import Flask, request, jsonify  
import swisseph as swe  
import os  
from datetime import datetime  
import sys  

app = Flask(__name__)  
swe.set_ephe_path('.')  # Changed to root where seas_18.se1 is

# Force stdout to flush immediately  
sys.stdout.flush()  

# Check what ephemeris is being used at startup
print("=" * 50)
print("EPHEMERIS CHECK AT STARTUP")
print("=" * 50)
print("Current directory:", os.getcwd())
print("Files in current dir:", os.listdir('.'))
# Check if we have the ephemeris files
ephe_files = [f for f in os.listdir('.') if f.endswith('.se1')]
print("Ephemeris files found:", ephe_files)
if not ephe_files:
    print("WARNING: No .se1 files found - will fall back to Moshier!")
else:
    print("SUCCESS: Using Swiss Ephemeris with JPL data")
print("=" * 50)

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
    'North Node': swe.TRUE_NODE,
    # Asteroids
    'Ceres': swe.CERES,
    'Pallas': swe.PALLAS,
    'Juno': swe.JUNO,
    'Vesta': swe.VESTA,
    'Pholus': swe.PHOLUS,
    # Lilith (Mean Black Moon)
    'Black Moon Lilith': swe.MEAN_APOG,
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
        "version": "2.0",  
        "endpoints": {  
            "/calculate": "POST - Calculate all planets, asteroids, and houses",  
            "/": "GET - This status page"  
        },
        "bodies": list(PLANETS.keys()) + ['South Node', 'White Moon Selena', 'Vertex', 'Part of Fortune'],
        "ephemeris_files": [f for f in os.listdir('.') if f.endswith('.se1')]
    })  

@app.route('/calculate', methods=['POST'])  
def calculate():  
    try:  
        data = request.json  
        birth_date = data['birthDate']        # format "YYYY-MM-DD"  
        birth_time = data['time']             # format "HH:MM" (24h)  
        latitude = float(data['latitude'])    # decimal degrees, North=positive, South=negative  
        longitude = float(data['longitude'])  # decimal degrees, East=positive, West=negative  

        # Log input for debugging
        app.logger.info(f"INPUT: {birth_date} {birth_time} at ({latitude}, {longitude})")

        year, month, day = map(int, birth_date.split('-'))  
        hour, minute = map(int, birth_time.split(':'))  
        time_decimal = hour + minute/60.0  

        # Julian Day (UT)  
        jd = swe.julday(year, month, day, time_decimal)  

        # Calculate planet positions  
        planets = []  
        for name, planet_id in PLANETS.items():  
            try:
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
            except Exception as e:
                app.logger.warning(f"Could not calculate {name}: {e}")

        # Add South Node (opposite North Node)
        north_node = next((p for p in planets if p['name'] == 'North Node'), None)
        if north_node:
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

        # Add White Moon Selena (if available)
        try:
            selena_result = swe.calc_ut(jd, 56)  # SE_WHITE_MOON = 56
            selena_lon = selena_result[0][0]
            planets.append({
                'name': 'White Moon Selena',
                'fullDegree': normalize_degree(selena_lon),
                'degreeInSign': normalize_degree(selena_lon) % 30.0,
                'sign': get_zodiac_sign(selena_lon),
                'latitude': selena_result[0][1],
                'distance': selena_result[0][2],
                'speed': selena_result[0][3],
                'isRetro': selena_result[0][3] < 0
            })
        except Exception as e:
            app.logger.warning(f"Could not calculate White Moon Selena: {e}")

        # Calculate houses (Placidus) - Python binding signature
        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')  # Explicitly use Placidus

        asc_deg = normalize_degree(ascmc[0])  
        mc_deg = normalize_degree(ascmc[1])
        vertex_deg = normalize_degree(ascmc[3])  # Vertex is ascmc[3]
        
        # Calculate Descendant and IC
        desc_deg = normalize_degree(asc_deg + 180)
        ic_deg = normalize_degree(mc_deg + 180)

        # Log house calculation for debugging
        app.logger.info(f"HOUSES: ASC={asc_deg:.4f}, MC={mc_deg:.4f}, Vertex={vertex_deg:.4f}")

        # Add Vertex to planets list
        planets.append({
            'name': 'Vertex',
            'fullDegree': vertex_deg,
            'degreeInSign': vertex_deg % 30.0,
            'sign': get_zodiac_sign(vertex_deg),
            'latitude': 0,
            'distance': 0,
            'speed': 0,
            'isRetro': False
        })

        # Calculate Part of Fortune
        sun_data = next((p for p in planets if p['name'] == 'Sun'), None)
        moon_data = next((p for p in planets if p['name'] == 'Moon'), None)
        
        if sun_data and moon_data:
            sun_lon = sun_data['fullDegree']
            moon_lon = moon_data['fullDegree']
            
            # Determine if day or night chart
            # Day chart: Sun is above horizon (between ASC and DESC via MC)
            # Simplified: check if Sun is in upper hemisphere
            if desc_deg <= asc_deg:
                is_day_chart = desc_deg <= sun_lon or sun_lon < asc_deg
            else:
                is_day_chart = desc_deg <= sun_lon < asc_deg
            
            if is_day_chart:
                pof_deg = normalize_degree(asc_deg + moon_lon - sun_lon)
            else:
                pof_deg = normalize_degree(asc_deg + sun_lon - moon_lon)
            
            planets.append({
                'name': 'Part of Fortune',
                'fullDegree': pof_deg,
                'degreeInSign': pof_deg % 30.0,
                'sign': get_zodiac_sign(pof_deg),
                'latitude': 0,
                'distance': 0,
                'speed': 0,
                'isRetro': False,
                'is_day_chart': is_day_chart
            })

        # Build houses object with all angles
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
            'descendant': {
                'degree': desc_deg,
                'degreeInSign': desc_deg % 30.0,
                'sign': get_zodiac_sign(desc_deg)
            },
            'ic': {
                'degree': ic_deg,
                'degreeInSign': ic_deg % 30.0,
                'sign': get_zodiac_sign(ic_deg)
            },
            'vertex': {
                'degree': vertex_deg,
                'degreeInSign': vertex_deg % 30.0,
                'sign': get_zodiac_sign(vertex_deg)
            },
            'cusps': []  
        }  

        for i in range(12):
            cusp_deg = normalize_degree(cusps[i])  
            houses['cusps'].append({  
                'house': i + 1,
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

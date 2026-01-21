from flask import Flask, request, jsonify
import swisseph as swe
import os
from datetime import datetime
import sys

app = Flask(__name__)
swe.set_ephe_path('.')

# Force stdout to flush immediately
sys.stdout.flush()

# Check what ephemeris is being used at startup
print("=" * 50)
print("EPHEMERIS CHECK AT STARTUP")
print("=" * 50)
print("Current directory:", os.getcwd())
print("Files in current dir:", os.listdir('.'))
ephe_files = [f for f in os.listdir('.') if f.endswith('.se1')]
print("Ephemeris files found:", ephe_files)
if not ephe_files:
    print("WARNING: No .se1 files found - will fall back to Moshier!")
else:
    print("SUCCESS: Using Swiss Ephemeris with JPL data")
print("=" * 50)

# Planet constants
# Note: We calculate all three Lilith variants but output with specific names
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
    'Ceres': swe.CERES,
    'Pallas': swe.PALLAS,
    'Juno': swe.JUNO,
    'Vesta': swe.VESTA,
    'Pholus': swe.PHOLUS,
    # Lilith variants - we'll rename these in output
    'Mean Lilith': swe.MEAN_APOG,
    'True Lilith': swe.OSCU_APOG,
    'Interpolated Lilith': swe.INTP_APOG,
}

def normalize_degree(deg):
    deg = deg % 360.0
    if deg < 0:
        deg += 360.0
    return deg

def get_zodiac_sign(degree):
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    index = int(normalize_degree(degree) / 30)
    return signs[index]

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "Swiss Ephemeris API is running",
        "version": "2.2",
        "endpoints": {
            "/calculate": "POST - Calculate all planets, asteroids, and houses",
            "/": "GET - This status page"
        },
        "bodies": [
            "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
            "Uranus", "Neptune", "Pluto", "Chiron", "North Node", "South Node",
            "Ceres", "Pallas", "Juno", "Vesta", "Pholus",
            "Black Moon Lilith (Interpolated)", "Mean Lilith", "True Lilith",
            "White Moon Selena (Interpolated Priapus)", "Mean Priapus", "True Priapus",
            "Selena h56 (Russian)", "Vertex", "Part of Fortune"
        ],
        "ephemeris_files": [f for f in os.listdir('.') if f.endswith('.se1')]
    })

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        birth_date = data['birthDate']
        birth_time = data['time']
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])

        print(f"INPUT: {birth_date} {birth_time} at ({latitude}, {longitude})")

        year, month, day = map(int, birth_date.split('-'))
        hour, minute = map(int, birth_time.split(':'))
        time_decimal = hour + minute / 60.0

        # Julian Day (UT)
        jd = swe.julday(year, month, day, time_decimal)
        print(f"Julian Day: {jd}")

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
                    'isRetro': speed < 0
                })
            except Exception as e:
                print(f"Could not calculate {name}: {e}")

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

        # ==============================================
        # LILITH AND PRIAPUS (SELENA) CALCULATIONS
        # ==============================================
        # Interpolated Lilith is the most accurate for Western astrology
        # Its opposite (Interpolated Priapus) = White Moon Selena (lunar perigee)
        
        # Get Interpolated Lilith and output as "Black Moon Lilith" (standard Western name)
        interp_lilith = next((p for p in planets if p['name'] == 'Interpolated Lilith'), None)
        if interp_lilith:
            # Add as "Black Moon Lilith" - the standard Western astrology name
            planets.append({
                'name': 'Black Moon Lilith',
                'fullDegree': interp_lilith['fullDegree'],
                'degreeInSign': interp_lilith['degreeInSign'],
                'sign': interp_lilith['sign'],
                'latitude': interp_lilith['latitude'],
                'distance': interp_lilith['distance'],
                'speed': interp_lilith['speed'],
                'isRetro': interp_lilith['isRetro']
            })
            
            # Add White Moon Selena as opposite of Interpolated Lilith (astronomically real lunar perigee)
            selena_deg = normalize_degree(interp_lilith['fullDegree'] + 180.0)
            planets.append({
                'name': 'White Moon Selena',
                'fullDegree': selena_deg,
                'degreeInSign': selena_deg % 30.0,
                'sign': get_zodiac_sign(selena_deg),
                'latitude': -interp_lilith['latitude'],
                'distance': interp_lilith['distance'],
                'speed': interp_lilith['speed'],
                'isRetro': False
            })

        # Add Mean Priapus (opposite Mean Lilith) - for reference
        mean_lilith = next((p for p in planets if p['name'] == 'Mean Lilith'), None)
        if mean_lilith:
            mean_priapus_deg = normalize_degree(mean_lilith['fullDegree'] + 180.0)
            planets.append({
                'name': 'Mean Priapus',
                'fullDegree': mean_priapus_deg,
                'degreeInSign': mean_priapus_deg % 30.0,
                'sign': get_zodiac_sign(mean_priapus_deg),
                'latitude': -mean_lilith['latitude'],
                'distance': mean_lilith['distance'],
                'speed': mean_lilith['speed'],
                'isRetro': False
            })

        # Add True Priapus (opposite True Lilith) - for reference
        true_lilith = next((p for p in planets if p['name'] == 'True Lilith'), None)
        if true_lilith:
            true_priapus_deg = normalize_degree(true_lilith['fullDegree'] + 180.0)
            planets.append({
                'name': 'True Priapus',
                'fullDegree': true_priapus_deg,
                'degreeInSign': true_priapus_deg % 30.0,
                'sign': get_zodiac_sign(true_priapus_deg),
                'latitude': -true_lilith['latitude'],
                'distance': true_lilith['distance'],
                'speed': true_lilith['speed'],
                'isRetro': False
            })

        # Add Selena h56 (Russian/Avestan tradition, ~7 year orbit) - fictional but used by some
        try:
            selena_h56_result = swe.calc_ut(jd, 56)
            selena_h56_lon = selena_h56_result[0][0]
            planets.append({
                'name': 'Selena h56',
                'fullDegree': normalize_degree(selena_h56_lon),
                'degreeInSign': normalize_degree(selena_h56_lon) % 30.0,
                'sign': get_zodiac_sign(selena_h56_lon),
                'latitude': selena_h56_result[0][1],
                'distance': selena_h56_result[0][2],
                'speed': selena_h56_result[0][3],
                'isRetro': selena_h56_result[0][3] < 0
            })
        except Exception as e:
            print(f"Could not calculate Selena h56: {e}")

        # ============================================================
        # HOUSE CALCULATION - Using swe.houses_ex for more precision
        # ============================================================
        houses_result = swe.houses_ex(jd, latitude, longitude, b'P')
        cusps = houses_result[0]
        ascmc = houses_result[1]

        asc_deg = normalize_degree(ascmc[0])
        mc_deg = normalize_degree(ascmc[1])
        armc = ascmc[2]  # Sidereal time in degrees
        vertex_deg = normalize_degree(ascmc[3])

        # Descendant and IC
        desc_deg = normalize_degree(asc_deg + 180)
        ic_deg = normalize_degree(mc_deg + 180)

        print(f"HOUSES: ASC={asc_deg:.4f}, MC={mc_deg:.4f}, ARMC={armc:.4f}, Vertex={vertex_deg:.4f}")

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

            # Normalize positions relative to ASC
            sun_from_asc = normalize_degree(sun_lon - asc_deg)
            # If sun_from_asc < 180, Sun is in lower hemisphere (houses 1-6) = night
            # If sun_from_asc >= 180, Sun is in upper hemisphere (houses 7-12) = day
            is_day_chart = sun_from_asc >= 180

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

        # Build houses object
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
            'armc': armc,
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
        print(f"MAIN ERROR: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'message': 'Calculation failed',
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

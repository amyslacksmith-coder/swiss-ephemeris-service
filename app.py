from flask import Flask, request, jsonify
import swisseph as swe
import os
from datetime import datetime
import sys

app = Flask(__name__)
swe.set_ephe_path('.')

sys.stdout.flush()

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
    'Mean Lilith': swe.MEAN_APOG,
    'True Lilith': swe.OSCU_APOG,
    'Interpolated Lilith': swe.INTP_APOG,
}

HOUSE_SYSTEMS = {
    'P': 'Placidus',
    'K': 'Koch',
    'E': 'Equal',
    'W': 'Whole Sign',
    'C': 'Campanus',
    'R': 'Regiomontanus',
    'B': 'Alcabitius',
    'O': 'Porphyry',
    'T': 'Topocentric',
    'M': 'Morinus'
}

# Aspect definitions: name, angle, default orb for lights (Sun/Moon), default orb for planets
ASPECTS = {
    'conjunction': {'angle': 0, 'orb_lights': 10, 'orb_planets': 8, 'symbol': '☌'},
    'opposition': {'angle': 180, 'orb_lights': 10, 'orb_planets': 8, 'symbol': '☍'},
    'trine': {'angle': 120, 'orb_lights': 8, 'orb_planets': 6, 'symbol': '△'},
    'square': {'angle': 90, 'orb_lights': 8, 'orb_planets': 6, 'symbol': '□'},
    'sextile': {'angle': 60, 'orb_lights': 6, 'orb_planets': 4, 'symbol': '⚹'},
    'quincunx': {'angle': 150, 'orb_lights': 3, 'orb_planets': 2, 'symbol': '⚻'},
    'semi_sextile': {'angle': 30, 'orb_lights': 2, 'orb_planets': 1, 'symbol': '⚺'},
    'semi_square': {'angle': 45, 'orb_lights': 2, 'orb_planets': 1, 'symbol': '∠'},
    'sesquiquadrate': {'angle': 135, 'orb_lights': 2, 'orb_planets': 1, 'symbol': '⚼'},
    'quintile': {'angle': 72, 'orb_lights': 2, 'orb_planets': 1, 'symbol': 'Q'},
    'biquintile': {'angle': 144, 'orb_lights': 2, 'orb_planets': 1, 'symbol': 'bQ'}
}

# Planets to include in aspect calculations (main bodies only)
ASPECT_PLANETS = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron', 'North Node', 'Black Moon Lilith']

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

def is_light(planet_name):
    return planet_name in ['Sun', 'Moon']

def calculate_aspect(planet1, planet2):
    """Calculate aspect between two planets if within orb"""
    deg1 = planet1['fullDegree']
    deg2 = planet2['fullDegree']
    speed1 = planet1.get('speed', 0)
    speed2 = planet2.get('speed', 0)
    
    # Calculate angle between planets
    diff = abs(deg1 - deg2)
    if diff > 180:
        diff = 360 - diff
    
    # Determine orb based on whether lights are involved
    use_light_orb = is_light(planet1['name']) or is_light(planet2['name'])
    
    # Check each aspect type
    for aspect_name, aspect_data in ASPECTS.items():
        target_angle = aspect_data['angle']
        orb = aspect_data['orb_lights'] if use_light_orb else aspect_data['orb_planets']
        
        actual_orb = abs(diff - target_angle)
        
        if actual_orb <= orb:
            # Determine if applying or separating
            # Applying = aspect getting tighter, Separating = aspect getting looser
            # We need to check if the faster planet is moving toward or away from exact
            
            raw_diff = deg1 - deg2
            if raw_diff < -180:
                raw_diff += 360
            elif raw_diff > 180:
                raw_diff -= 360
            
            relative_speed = speed1 - speed2
            
            # For conjunction/opposition logic differs from other aspects
            if target_angle == 0:
                is_applying = (raw_diff > 0 and relative_speed < 0) or (raw_diff < 0 and relative_speed > 0)
            elif target_angle == 180:
                if abs(raw_diff) > 180:
                    is_applying = relative_speed > 0 if raw_diff > 0 else relative_speed < 0
                else:
                    is_applying = relative_speed < 0 if raw_diff > 0 else relative_speed > 0
            else:
                # For other aspects, simplified logic
                is_applying = actual_orb > 0 and (
                    (raw_diff > 0 and relative_speed < 0) or 
                    (raw_diff < 0 and relative_speed > 0)
                )
            
            return {
                'aspect': aspect_name,
                'angle': target_angle,
                'symbol': aspect_data['symbol'],
                'orb': round(actual_orb, 2),
                'orb_allowed': orb,
                'is_applying': is_applying,
                'is_exact': actual_orb < 0.5
            }
    
    return None

def calculate_all_aspects(planets, include_angles=False, asc_deg=None, mc_deg=None):
    """Calculate all aspects between planets"""
    aspects = []
    
    # Filter to only aspect-worthy planets
    aspect_bodies = [p for p in planets if p['name'] in ASPECT_PLANETS]
    
    # Optionally add angles
    if include_angles and asc_deg is not None and mc_deg is not None:
        aspect_bodies.append({
            'name': 'Ascendant',
            'fullDegree': asc_deg,
            'speed': 0
        })
        aspect_bodies.append({
            'name': 'Midheaven',
            'fullDegree': mc_deg,
            'speed': 0
        })
    
    # Calculate aspects between all pairs
    for i in range(len(aspect_bodies)):
        for j in range(i + 1, len(aspect_bodies)):
            planet1 = aspect_bodies[i]
            planet2 = aspect_bodies[j]
            
            aspect = calculate_aspect(planet1, planet2)
            
            if aspect:
                aspects.append({
                    'planet1': planet1['name'],
                    'planet2': planet2['name'],
                    **aspect
                })
    
    # Sort by orb (tightest first)
    aspects.sort(key=lambda x: x['orb'])
    
    return aspects

def detect_aspect_patterns(aspects):
    """Detect major aspect patterns like Grand Trine, T-Square, etc."""
    patterns = []
    
    # Build adjacency for pattern detection
    trines = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'trine']
    squares = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'square']
    oppositions = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'opposition']
    sextiles = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'sextile']
    
    # Grand Trine: 3 planets all trine each other
    all_planets = set()
    for t in trines:
        all_planets.add(t[0])
        all_planets.add(t[1])
    
    for p1 in all_planets:
        for p2 in all_planets:
            for p3 in all_planets:
                if p1 < p2 < p3:  # Avoid duplicates
                    has_t1 = (p1, p2) in trines or (p2, p1) in trines
                    has_t2 = (p2, p3) in trines or (p3, p2) in trines
                    has_t3 = (p1, p3) in trines or (p3, p1) in trines
                    if has_t1 and has_t2 and has_t3:
                        patterns.append({
                            'pattern': 'Grand Trine',
                            'planets': [p1, p2, p3]
                        })
    
    # T-Square: 2 planets in opposition, both square a third
    for opp in oppositions:
        p1, p2 = opp
        for sq in squares:
            sq_planet = None
            if sq[0] == p1 or sq[1] == p1:
                sq_planet = sq[1] if sq[0] == p1 else sq[0]
            if sq_planet:
                # Check if sq_planet also squares p2
                has_sq2 = (p2, sq_planet) in squares or (sq_planet, p2) in squares
                if has_sq2:
                    pattern_planets = sorted([p1, p2, sq_planet])
                    pattern = {
                        'pattern': 'T-Square',
                        'planets': pattern_planets,
                        'apex': sq_planet
                    }
                    if pattern not in patterns:
                        patterns.append(pattern)
    
    # Grand Cross: 4 planets, 2 oppositions, all square each other
    if len(oppositions) >= 2:
        for i, opp1 in enumerate(oppositions):
            for opp2 in oppositions[i+1:]:
                p1, p2 = opp1
                p3, p4 = opp2
                # Check all 4 squares exist
                has_sq1 = (p1, p3) in squares or (p3, p1) in squares
                has_sq2 = (p1, p4) in squares or (p4, p1) in squares
                has_sq3 = (p2, p3) in squares or (p3, p2) in squares
                has_sq4 = (p2, p4) in squares or (p4, p2) in squares
                if has_sq1 and has_sq2 and has_sq3 and has_sq4:
                    patterns.append({
                        'pattern': 'Grand Cross',
                        'planets': sorted([p1, p2, p3, p4])
                    })
    
    # Yod (Finger of God): 2 planets sextile each other, both quincunx a third
    quincunxes = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'quincunx']
    for sx in sextiles:
        p1, p2 = sx
        for qx in quincunxes:
            apex = None
            if qx[0] == p1 or qx[1] == p1:
                apex = qx[1] if qx[0] == p1 else qx[0]
            if apex and apex != p2:
                # Check if apex also quincunx p2
                has_qx2 = (p2, apex) in quincunxes or (apex, p2) in quincunxes
                if has_qx2:
                    pattern = {
                        'pattern': 'Yod',
                        'planets': sorted([p1, p2, apex]),
                        'apex': apex
                    }
                    if pattern not in patterns:
                        patterns.append(pattern)
    
    return patterns

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "Swiss Ephemeris API is running",
        "version": "2.5",
        "endpoints": {
            "/calculate": "POST - Calculate all planets, asteroids, houses, and aspects",
            "/": "GET - This status page"
        },
        "house_systems": HOUSE_SYSTEMS,
        "aspects": list(ASPECTS.keys()),
        "bodies": [
            "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
            "Uranus", "Neptune", "Pluto", "Chiron", "North Node", "South Node",
            "Ceres", "Pallas", "Juno", "Vesta", "Pholus",
            "Black Moon Lilith", "Mean Lilith", "True Lilith",
            "White Moon Selena", "Mean Priapus", "True Priapus",
            "Selena h56", "Vertex", "Part of Fortune"
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
        house_system = str(data.get('houseSystem', 'P')).upper()
        include_aspects = data.get('includeAspects', True)
        include_patterns = data.get('includePatterns', True)
        include_angle_aspects = data.get('includeAngleAspects', True)
        
        if house_system not in HOUSE_SYSTEMS:
            house_system = 'P'

        print(f"INPUT: {birth_date} {birth_time} at ({latitude}, {longitude}) house_system={house_system} ({HOUSE_SYSTEMS[house_system]})")

        year, month, day = map(int, birth_date.split('-'))
        hour, minute = map(int, birth_time.split(':'))
        time_decimal = hour + minute / 60.0

        jd = swe.julday(year, month, day, time_decimal)
        print(f"Julian Day: {jd}")

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

        mean_lilith = next((p for p in planets if p['name'] == 'Mean Lilith'), None)
        if mean_lilith:
            planets.append({
                'name': 'Black Moon Lilith',
                'fullDegree': mean_lilith['fullDegree'],
                'degreeInSign': mean_lilith['degreeInSign'],
                'sign': mean_lilith['sign'],
                'latitude': mean_lilith['latitude'],
                'distance': mean_lilith['distance'],
                'speed': mean_lilith['speed'],
                'isRetro': mean_lilith['isRetro']
            })
            
            selena_deg = normalize_degree(mean_lilith['fullDegree'] + 180.0)
            planets.append({
                'name': 'White Moon Selena',
                'fullDegree': selena_deg,
                'degreeInSign': selena_deg % 30.0,
                'sign': get_zodiac_sign(selena_deg),
                'latitude': -mean_lilith['latitude'],
                'distance': mean_lilith['distance'],
                'speed': mean_lilith['speed'],
                'isRetro': False
            })

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

        hsys = house_system.encode('ascii')[0]
        houses_result = swe.houses_ex(jd, latitude, longitude, hsys)
        cusps = houses_result[0]
        ascmc = houses_result[1]

        asc_deg = normalize_degree(ascmc[0])
        mc_deg = normalize_degree(ascmc[1])
        armc = ascmc[2]
        vertex_deg = normalize_degree(ascmc[3])

        desc_deg = normalize_degree(asc_deg + 180)
        ic_deg = normalize_degree(mc_deg + 180)

        print(f"HOUSES ({HOUSE_SYSTEMS[house_system]}): ASC={asc_deg:.4f}, MC={mc_deg:.4f}, ARMC={armc:.4f}, Vertex={vertex_deg:.4f}")

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

        sun_data = next((p for p in planets if p['name'] == 'Sun'), None)
        moon_data = next((p for p in planets if p['name'] == 'Moon'), None)

        if sun_data and moon_data:
            sun_lon = sun_data['fullDegree']
            moon_lon = moon_data['fullDegree']
            sun_from_asc = normalize_degree(sun_lon - asc_deg)
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

        houses = {
            'system': house_system,
            'system_name': HOUSE_SYSTEMS.get(house_system, 'Unknown'),
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

        # Calculate aspects
        aspects = []
        patterns = []
        if include_aspects:
            aspects = calculate_all_aspects(planets, include_angle_aspects, asc_deg, mc_deg)
            print(f"ASPECTS: Found {len(aspects)} aspects")
            
            if include_patterns:
                patterns = detect_aspect_patterns(aspects)
                print(f"PATTERNS: Found {len(patterns)} patterns")

        return jsonify({
            'birthDate': birth_date,
            'birthTime': birth_time,
            'latitude': latitude,
            'longitude': longitude,
            'julianDay': jd,
            'houseSystem': house_system,
            'houseSystemName': HOUSE_SYSTEMS.get(house_system, 'Unknown'),
            'planets': planets,
            'houses': houses,
            'aspects': aspects,
            'aspectPatterns': patterns,
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

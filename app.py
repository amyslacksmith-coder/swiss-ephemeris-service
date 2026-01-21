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
    'R': 'Regiomontanus',
    'C': 'Campanus',
    'B': 'Alcabitius',
    'O': 'Porphyry',
    'T': 'Topocentric',
    'M': 'Morinus',
    'X': 'Meridian',
    'V': 'Vehlow Equal'
}

ASPECTS = {
    'conjunction': {'angle': 0, 'orb_lights': 10, 'orb_planets': 8, 'symbol': '☌', 'type': 'major'},
    'opposition': {'angle': 180, 'orb_lights': 10, 'orb_planets': 8, 'symbol': '☍', 'type': 'major'},
    'trine': {'angle': 120, 'orb_lights': 8, 'orb_planets': 6, 'symbol': '△', 'type': 'major'},
    'square': {'angle': 90, 'orb_lights': 8, 'orb_planets': 6, 'symbol': '□', 'type': 'major'},
    'sextile': {'angle': 60, 'orb_lights': 6, 'orb_planets': 4, 'symbol': '⚹', 'type': 'major'},
    'quincunx': {'angle': 150, 'orb_lights': 3, 'orb_planets': 2, 'symbol': '⚻', 'type': 'minor'},
    'semi_sextile': {'angle': 30, 'orb_lights': 2, 'orb_planets': 1, 'symbol': '⚺', 'type': 'minor'},
    'semi_square': {'angle': 45, 'orb_lights': 2, 'orb_planets': 1, 'symbol': '∠', 'type': 'minor'},
    'sesquiquadrate': {'angle': 135, 'orb_lights': 2, 'orb_planets': 1, 'symbol': '⚼', 'type': 'minor'},
    'quintile': {'angle': 72, 'orb_lights': 2, 'orb_planets': 1, 'symbol': 'Q', 'type': 'minor'},
    'biquintile': {'angle': 144, 'orb_lights': 2, 'orb_planets': 1, 'symbol': 'bQ', 'type': 'minor'},
    'septile': {'angle': 51.43, 'orb_lights': 1, 'orb_planets': 1, 'symbol': 'S', 'type': 'minor'},
    'novile': {'angle': 40, 'orb_lights': 1, 'orb_planets': 1, 'symbol': 'N', 'type': 'minor'},
    'decile': {'angle': 36, 'orb_lights': 1, 'orb_planets': 1, 'symbol': 'D', 'type': 'minor'},
    'parallel': {'angle': 0, 'orb_lights': 1, 'orb_planets': 1, 'symbol': '∥', 'type': 'declination'},
    'contraparallel': {'angle': 0, 'orb_lights': 1, 'orb_planets': 1, 'symbol': '#', 'type': 'declination'}
}

ASPECT_PLANETS = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 
                  'Uranus', 'Neptune', 'Pluto', 'Chiron', 'North Node', 'Black Moon Lilith']

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

ELEMENTS = {
    'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
    'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
    'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
    'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
}

MODALITIES = {
    'Aries': 'Cardinal', 'Cancer': 'Cardinal', 'Libra': 'Cardinal', 'Capricorn': 'Cardinal',
    'Taurus': 'Fixed', 'Leo': 'Fixed', 'Scorpio': 'Fixed', 'Aquarius': 'Fixed',
    'Gemini': 'Mutable', 'Virgo': 'Mutable', 'Sagittarius': 'Mutable', 'Pisces': 'Mutable'
}

POLARITIES = {
    'Aries': 'Positive', 'Gemini': 'Positive', 'Leo': 'Positive', 
    'Libra': 'Positive', 'Sagittarius': 'Positive', 'Aquarius': 'Positive',
    'Taurus': 'Negative', 'Cancer': 'Negative', 'Virgo': 'Negative',
    'Scorpio': 'Negative', 'Capricorn': 'Negative', 'Pisces': 'Negative'
}

# Planetary dignities
DIGNITIES = {
    'Sun': {'domicile': ['Leo'], 'exaltation': ['Aries'], 'detriment': ['Aquarius'], 'fall': ['Libra']},
    'Moon': {'domicile': ['Cancer'], 'exaltation': ['Taurus'], 'detriment': ['Capricorn'], 'fall': ['Scorpio']},
    'Mercury': {'domicile': ['Gemini', 'Virgo'], 'exaltation': ['Virgo'], 'detriment': ['Sagittarius', 'Pisces'], 'fall': ['Pisces']},
    'Venus': {'domicile': ['Taurus', 'Libra'], 'exaltation': ['Pisces'], 'detriment': ['Aries', 'Scorpio'], 'fall': ['Virgo']},
    'Mars': {'domicile': ['Aries', 'Scorpio'], 'exaltation': ['Capricorn'], 'detriment': ['Libra', 'Taurus'], 'fall': ['Cancer']},
    'Jupiter': {'domicile': ['Sagittarius', 'Pisces'], 'exaltation': ['Cancer'], 'detriment': ['Gemini', 'Virgo'], 'fall': ['Capricorn']},
    'Saturn': {'domicile': ['Capricorn', 'Aquarius'], 'exaltation': ['Libra'], 'detriment': ['Cancer', 'Leo'], 'fall': ['Aries']},
    'Uranus': {'domicile': ['Aquarius'], 'exaltation': ['Scorpio'], 'detriment': ['Leo'], 'fall': ['Taurus']},
    'Neptune': {'domicile': ['Pisces'], 'exaltation': ['Leo'], 'detriment': ['Virgo'], 'fall': ['Aquarius']},
    'Pluto': {'domicile': ['Scorpio'], 'exaltation': ['Aries'], 'detriment': ['Taurus'], 'fall': ['Libra']}
}

# Fixed stars (longitude as of J2000, with ~50" annual precession)
FIXED_STARS = {
    'Algol': {'longitude': 56.17, 'nature': 'Saturn/Jupiter', 'meaning': 'Intense, passionate, misfortune if afflicted'},
    'Alcyone': {'longitude': 60.0, 'nature': 'Moon/Mars', 'meaning': 'Ambition, honor, eminence'},
    'Aldebaran': {'longitude': 69.85, 'nature': 'Mars', 'meaning': 'Success, intelligence, integrity - Royal Star'},
    'Rigel': {'longitude': 76.97, 'nature': 'Jupiter/Saturn', 'meaning': 'Technical/artistic ability, wealth'},
    'Capella': {'longitude': 81.85, 'nature': 'Mars/Mercury', 'meaning': 'Honors, wealth, public position'},
    'Sirius': {'longitude': 104.07, 'nature': 'Jupiter/Mars', 'meaning': 'Ambition, fame, passion, danger - brightest star'},
    'Canopus': {'longitude': 104.97, 'nature': 'Saturn/Jupiter', 'meaning': 'Voyages, education, piety'},
    'Castor': {'longitude': 110.35, 'nature': 'Mercury', 'meaning': 'Success, distinction, sudden fame or loss'},
    'Pollux': {'longitude': 113.22, 'nature': 'Mars', 'meaning': 'Audacity, cruelty, athletic'},
    'Procyon': {'longitude': 115.62, 'nature': 'Mercury/Mars', 'meaning': 'Activity, violence, sudden success then loss'},
    'Regulus': {'longitude': 149.83, 'nature': 'Mars/Jupiter', 'meaning': 'Success, leadership, ambition - Royal Star'},
    'Zosma': {'longitude': 161.32, 'nature': 'Saturn/Venus', 'meaning': 'Benefit through disgrace, egotism'},
    'Denebola': {'longitude': 171.55, 'nature': 'Saturn/Venus', 'meaning': 'Swift judgment, misfortune, honors'},
    'Vindemiatrix': {'longitude': 189.78, 'nature': 'Saturn/Mercury', 'meaning': 'Widowhood, loss of partner'},
    'Spica': {'longitude': 203.83, 'nature': 'Venus/Mars', 'meaning': 'Success, renown, wealth, love of arts'},
    'Arcturus': {'longitude': 204.15, 'nature': 'Mars/Jupiter', 'meaning': 'Success through self-determination'},
    'Alphecca': {'longitude': 222.17, 'nature': 'Venus/Mercury', 'meaning': 'Honor, artistic ability'},
    'Antares': {'longitude': 249.77, 'nature': 'Mars/Jupiter', 'meaning': 'Success, suspicion, violence - Royal Star'},
    'Vega': {'longitude': 285.45, 'nature': 'Venus/Mercury', 'meaning': 'Idealism, refinement, changeability'},
    'Altair': {'longitude': 301.82, 'nature': 'Mars/Jupiter', 'meaning': 'Bold, confident, sudden wealth'},
    'Deneb': {'longitude': 320.22, 'nature': 'Venus/Mercury', 'meaning': 'Ingenious mind, artistic'},
    'Fomalhaut': {'longitude': 333.87, 'nature': 'Venus/Mercury', 'meaning': 'Fame, occult interests - Royal Star'},
    'Scheat': {'longitude': 349.37, 'nature': 'Mars/Mercury', 'meaning': 'Misfortune, drowning, extreme sensitivity'}
}

# Arabic Parts formulas (Day formula, Night formula - some reverse)
ARABIC_PARTS = {
    'Part of Fortune': {'day': 'ASC + Moon - Sun', 'night': 'ASC + Sun - Moon'},
    'Part of Spirit': {'day': 'ASC + Sun - Moon', 'night': 'ASC + Moon - Sun'},
    'Part of Love': {'formula': 'ASC + Venus - Sun'},
    'Part of Marriage': {'formula': 'ASC + DESC - Venus'},
    'Part of Children': {'formula': 'ASC + Jupiter - Saturn'},
    'Part of Father': {'day': 'ASC + Sun - Saturn', 'night': 'ASC + Saturn - Sun'},
    'Part of Mother': {'day': 'ASC + Moon - Venus', 'night': 'ASC + Venus - Moon'},
    'Part of Siblings': {'formula': 'ASC + Jupiter - Saturn'},
    'Part of Death': {'formula': 'ASC + 8th cusp - Moon'},
    'Part of Illness': {'formula': 'ASC + Mars - Saturn'},
    'Part of Surgery': {'formula': 'ASC + Saturn - Mars'},
    'Part of Fame': {'formula': 'ASC + Jupiter - Sun'},
    'Part of Commerce': {'formula': 'ASC + Mercury - Sun'},
    'Part of Sudden Advancement': {'formula': 'ASC + Fortuna - Saturn'},
    'Part of Inheritance': {'formula': 'ASC + Moon - Saturn'},
    'Part of Hidden Enemies': {'formula': 'ASC + 12th cusp - ruler of 12th'}
}

def normalize_degree(deg):
    deg = deg % 360.0
    if deg < 0:
        deg += 360.0
    return deg

def get_zodiac_sign(degree):
    index = int(normalize_degree(degree) / 30)
    return SIGNS[index]

def get_sign_data(sign):
    return {
        'element': ELEMENTS.get(sign),
        'modality': MODALITIES.get(sign),
        'polarity': POLARITIES.get(sign)
    }

def is_light(planet_name):
    return planet_name in ['Sun', 'Moon']

def get_dignity(planet_name, sign):
    """Get essential dignity of planet in sign"""
    if planet_name not in DIGNITIES:
        return None
    
    dignities = DIGNITIES[planet_name]
    
    if sign in dignities.get('domicile', []):
        return {'type': 'domicile', 'strength': 5, 'description': 'Planet rules this sign - strongest placement'}
    elif sign in dignities.get('exaltation', []):
        return {'type': 'exaltation', 'strength': 4, 'description': 'Planet is exalted - very strong'}
    elif sign in dignities.get('detriment', []):
        return {'type': 'detriment', 'strength': -4, 'description': 'Planet is in detriment - weakened'}
    elif sign in dignities.get('fall', []):
        return {'type': 'fall', 'strength': -5, 'description': 'Planet is in fall - most challenged'}
    else:
        return {'type': 'peregrine', 'strength': 0, 'description': 'Planet has no essential dignity'}

def get_decan(degree):
    """Get decan (10° subdivision) and its ruler"""
    degree_in_sign = degree % 30
    decan_num = int(degree_in_sign / 10) + 1
    
    sign_index = int(degree / 30)
    
    # Chaldean decan rulers (traditional)
    decan_rulers = [
        ['Mars', 'Sun', 'Venus'],      # Aries
        ['Mercury', 'Moon', 'Saturn'], # Taurus
        ['Jupiter', 'Mars', 'Sun'],    # Gemini
        ['Venus', 'Mercury', 'Moon'],  # Cancer
        ['Saturn', 'Jupiter', 'Mars'], # Leo
        ['Sun', 'Venus', 'Mercury'],   # Virgo
        ['Moon', 'Saturn', 'Jupiter'], # Libra
        ['Mars', 'Sun', 'Venus'],      # Scorpio
        ['Mercury', 'Moon', 'Saturn'], # Sagittarius
        ['Jupiter', 'Mars', 'Sun'],    # Capricorn
        ['Venus', 'Mercury', 'Moon'],  # Aquarius
        ['Saturn', 'Jupiter', 'Mars']  # Pisces
    ]
    
    return {
        'decan': decan_num,
        'ruler': decan_rulers[sign_index][decan_num - 1],
        'degree_range': f"{(decan_num-1)*10}°-{decan_num*10}°"
    }

def get_term(degree):
    """Get Egyptian term/bound and its ruler"""
    degree_in_sign = degree % 30
    sign_index = int(degree / 30)
    
    # Egyptian terms (Ptolemaic)
    terms = [
        # Aries
        [(0, 6, 'Jupiter'), (6, 12, 'Venus'), (12, 20, 'Mercury'), (20, 25, 'Mars'), (25, 30, 'Saturn')],
        # Taurus
        [(0, 8, 'Venus'), (8, 14, 'Mercury'), (14, 22, 'Jupiter'), (22, 27, 'Saturn'), (27, 30, 'Mars')],
        # Gemini
        [(0, 6, 'Mercury'), (6, 12, 'Jupiter'), (12, 17, 'Venus'), (17, 24, 'Mars'), (24, 30, 'Saturn')],
        # Cancer
        [(0, 7, 'Mars'), (7, 13, 'Venus'), (13, 19, 'Mercury'), (19, 26, 'Jupiter'), (26, 30, 'Saturn')],
        # Leo
        [(0, 6, 'Jupiter'), (6, 11, 'Venus'), (11, 18, 'Saturn'), (18, 24, 'Mercury'), (24, 30, 'Mars')],
        # Virgo
        [(0, 7, 'Mercury'), (7, 17, 'Venus'), (17, 21, 'Jupiter'), (21, 28, 'Mars'), (28, 30, 'Saturn')],
        # Libra
        [(0, 6, 'Saturn'), (6, 14, 'Mercury'), (14, 21, 'Jupiter'), (21, 28, 'Venus'), (28, 30, 'Mars')],
        # Scorpio
        [(0, 7, 'Mars'), (7, 11, 'Venus'), (11, 19, 'Mercury'), (19, 24, 'Jupiter'), (24, 30, 'Saturn')],
        # Sagittarius
        [(0, 12, 'Jupiter'), (12, 17, 'Venus'), (17, 21, 'Mercury'), (21, 26, 'Saturn'), (26, 30, 'Mars')],
        # Capricorn
        [(0, 7, 'Mercury'), (7, 14, 'Jupiter'), (14, 22, 'Venus'), (22, 26, 'Saturn'), (26, 30, 'Mars')],
        # Aquarius
        [(0, 7, 'Mercury'), (7, 13, 'Venus'), (13, 20, 'Jupiter'), (20, 25, 'Mars'), (25, 30, 'Saturn')],
        # Pisces
        [(0, 12, 'Venus'), (12, 16, 'Jupiter'), (16, 19, 'Mercury'), (19, 28, 'Mars'), (28, 30, 'Saturn')]
    ]
    
    for start, end, ruler in terms[sign_index]:
        if start <= degree_in_sign < end:
            return {
                'ruler': ruler,
                'degree_range': f"{start}°-{end}°"
            }
    
    return None

def check_fixed_star_conjunctions(planets, orb=1.5):
    """Check for fixed star conjunctions"""
    conjunctions = []
    
    for planet in planets:
        if planet['name'] in ASPECT_PLANETS:
            planet_lon = planet['fullDegree']
            
            for star_name, star_data in FIXED_STARS.items():
                star_lon = star_data['longitude']
                diff = abs(planet_lon - star_lon)
                if diff > 180:
                    diff = 360 - diff
                
                if diff <= orb:
                    conjunctions.append({
                        'planet': planet['name'],
                        'star': star_name,
                        'orb': round(diff, 2),
                        'nature': star_data['nature'],
                        'meaning': star_data['meaning']
                    })
    
    return conjunctions

def calculate_aspect(planet1, planet2):
    deg1 = planet1['fullDegree']
    deg2 = planet2['fullDegree']
    speed1 = planet1.get('speed', 0)
    speed2 = planet2.get('speed', 0)
    
    diff = abs(deg1 - deg2)
    if diff > 180:
        diff = 360 - diff
    
    use_light_orb = is_light(planet1['name']) or is_light(planet2['name'])
    
    for aspect_name, aspect_data in ASPECTS.items():
        if aspect_data['type'] == 'declination':
            continue
            
        target_angle = aspect_data['angle']
        orb = aspect_data['orb_lights'] if use_light_orb else aspect_data['orb_planets']
        
        actual_orb = abs(diff - target_angle)
        
        if actual_orb <= orb:
            raw_diff = deg1 - deg2
            if raw_diff < -180:
                raw_diff += 360
            elif raw_diff > 180:
                raw_diff -= 360
            
            relative_speed = speed1 - speed2
            
            if target_angle == 0:
                is_applying = (raw_diff > 0 and relative_speed < 0) or (raw_diff < 0 and relative_speed > 0)
            elif target_angle == 180:
                if abs(raw_diff) > 180:
                    is_applying = relative_speed > 0 if raw_diff > 0 else relative_speed < 0
                else:
                    is_applying = relative_speed < 0 if raw_diff > 0 else relative_speed > 0
            else:
                is_applying = actual_orb > 0 and (
                    (raw_diff > 0 and relative_speed < 0) or 
                    (raw_diff < 0 and relative_speed > 0)
                )
            
            # Check if out of sign (dissociate)
            sign1 = get_zodiac_sign(deg1)
            sign2 = get_zodiac_sign(deg2)
            expected_sign_diff = target_angle / 30
            actual_sign_diff = abs(SIGNS.index(sign1) - SIGNS.index(sign2))
            if actual_sign_diff > 6:
                actual_sign_diff = 12 - actual_sign_diff
            is_dissociate = abs(actual_sign_diff - expected_sign_diff) > 0.5
            
            return {
                'aspect': aspect_name,
                'angle': target_angle,
                'symbol': aspect_data['symbol'],
                'type': aspect_data['type'],
                'orb': round(actual_orb, 2),
                'orb_allowed': orb,
                'is_applying': is_applying,
                'is_separating': not is_applying,
                'is_exact': actual_orb < 0.5,
                'is_dissociate': is_dissociate
            }
    
    return None

def calculate_declination_aspects(planets):
    """Calculate parallel and contraparallel aspects based on declination"""
    aspects = []
    aspect_bodies = [p for p in planets if p['name'] in ASPECT_PLANETS and 'latitude' in p]
    
    for i in range(len(aspect_bodies)):
        for j in range(i + 1, len(aspect_bodies)):
            p1 = aspect_bodies[i]
            p2 = aspect_bodies[j]
            
            # Using latitude as proxy for declination (proper declination requires more calc)
            dec1 = p1.get('latitude', 0)
            dec2 = p2.get('latitude', 0)
            
            diff = abs(dec1 - dec2)
            
            # Parallel - same declination
            if diff < 1.0:
                aspects.append({
                    'planet1': p1['name'],
                    'planet2': p2['name'],
                    'aspect': 'parallel',
                    'symbol': '∥',
                    'type': 'declination',
                    'orb': round(diff, 2),
                    'declination1': round(dec1, 2),
                    'declination2': round(dec2, 2)
                })
            
            # Contraparallel - opposite declination
            sum_dec = abs(dec1 + dec2)
            if sum_dec < 1.0 and (dec1 * dec2 < 0):  # Different signs
                aspects.append({
                    'planet1': p1['name'],
                    'planet2': p2['name'],
                    'aspect': 'contraparallel',
                    'symbol': '#',
                    'type': 'declination',
                    'orb': round(sum_dec, 2),
                    'declination1': round(dec1, 2),
                    'declination2': round(dec2, 2)
                })
    
    return aspects

def calculate_all_aspects(planets, include_angles=False, asc_deg=None, mc_deg=None):
    aspects = []
    
    aspect_bodies = [p for p in planets if p['name'] in ASPECT_PLANETS]
    
    if include_angles and asc_deg is not None and mc_deg is not None:
        aspect_bodies.append({'name': 'Ascendant', 'fullDegree': asc_deg, 'speed': 0})
        aspect_bodies.append({'name': 'Midheaven', 'fullDegree': mc_deg, 'speed': 0})
    
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
    
    aspects.sort(key=lambda x: x['orb'])
    
    return aspects

def detect_aspect_patterns(aspects, planets):
    patterns = []
    
    # Build adjacency lists
    conjunctions = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'conjunction']
    trines = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'trine']
    squares = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'square']
    oppositions = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'opposition']
    sextiles = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'sextile']
    quincunxes = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'quincunx']
    
    def has_aspect(p1, p2, aspect_list):
        return (p1, p2) in aspect_list or (p2, p1) in aspect_list
    
    all_planets_in_aspects = set()
    for a in aspects:
        all_planets_in_aspects.add(a['planet1'])
        all_planets_in_aspects.add(a['planet2'])
    
    # STELLIUM: 3+ planets conjunct within 8 degrees
    planet_positions = {p['name']: p['fullDegree'] for p in planets if p['name'] in ASPECT_PLANETS}
    for p1 in planet_positions:
        cluster = [p1]
        for p2 in planet_positions:
            if p1 != p2:
                diff = abs(planet_positions[p1] - planet_positions[p2])
                if diff > 180:
                    diff = 360 - diff
                if diff <= 8:
                    cluster.append(p2)
        if len(cluster) >= 3:
            cluster_sorted = sorted(set(cluster))
            pattern = {'pattern': 'Stellium', 'planets': cluster_sorted, 
                      'sign': get_zodiac_sign(planet_positions[p1]),
                      'description': f'{len(cluster_sorted)} planets concentrated - intense focus in this area'}
            if pattern not in patterns:
                patterns.append(pattern)
    
    # GRAND TRINE: 3 planets all trine each other
    all_trine_planets = set()
    for t in trines:
        all_trine_planets.add(t[0])
        all_trine_planets.add(t[1])
    
    for p1 in all_trine_planets:
        for p2 in all_trine_planets:
            for p3 in all_trine_planets:
                if p1 < p2 < p3:
                    if has_aspect(p1, p2, trines) and has_aspect(p2, p3, trines) and has_aspect(p1, p3, trines):
                        # Determine element
                        signs = []
                        for p in [p1, p2, p3]:
                            if p in planet_positions:
                                signs.append(get_zodiac_sign(planet_positions[p]))
                        elements = [ELEMENTS.get(s) for s in signs if s in ELEMENTS]
                        element = elements[0] if elements and len(set(elements)) == 1 else 'Mixed'
                        
                        patterns.append({
                            'pattern': 'Grand Trine',
                            'planets': [p1, p2, p3],
                            'element': element,
                            'description': f'{element} Grand Trine - natural talent and flow'
                        })
    
    # T-SQUARE: 2 planets in opposition, both square a third
    for opp in oppositions:
        p1, p2 = opp
        for sq in squares:
            sq_planet = None
            if sq[0] == p1 or sq[1] == p1:
                sq_planet = sq[1] if sq[0] == p1 else sq[0]
            if sq_planet and sq_planet != p2:
                if has_aspect(p2, sq_planet, squares):
                    pattern_planets = sorted([p1, p2, sq_planet])
                    # Determine modality of apex
                    apex_sign = get_zodiac_sign(planet_positions.get(sq_planet, 0)) if sq_planet in planet_positions else None
                    modality = MODALITIES.get(apex_sign) if apex_sign else None
                    
                    pattern = {
                        'pattern': 'T-Square',
                        'planets': pattern_planets,
                        'apex': sq_planet,
                        'modality': modality,
                        'description': f'Dynamic tension - {sq_planet} is the focal point for resolution'
                    }
                    if pattern not in patterns:
                        patterns.append(pattern)
    
    # GRAND CROSS: 4 planets, 2 oppositions, all square each other
    if len(oppositions) >= 2:
        for i, opp1 in enumerate(oppositions):
            for opp2 in oppositions[i+1:]:
                p1, p2 = opp1
                p3, p4 = opp2
                if has_aspect(p1, p3, squares) and has_aspect(p1, p4, squares) and \
                   has_aspect(p2, p3, squares) and has_aspect(p2, p4, squares):
                    patterns.append({
                        'pattern': 'Grand Cross',
                        'planets': sorted([p1, p2, p3, p4]),
                        'description': 'Maximum tension - powerful drive for achievement through obstacles'
                    })
    
    # YOD (Finger of God): 2 planets sextile, both quincunx a third
    for sx in sextiles:
        p1, p2 = sx
        for qx in quincunxes:
            apex = None
            if qx[0] == p1 or qx[1] == p1:
                apex = qx[1] if qx[0] == p1 else qx[0]
            if apex and apex != p2:
                if has_aspect(p2, apex, quincunxes):
                    pattern = {
                        'pattern': 'Yod',
                        'planets': sorted([p1, p2, apex]),
                        'apex': apex,
                        'description': f'Finger of Fate - {apex} is the point of destiny requiring adjustment'
                    }
                    if pattern not in patterns:
                        patterns.append(pattern)
    
    # KITE: Grand Trine + one planet opposite one of the trine planets (forming sextiles to the other two)
    for gt in [p for p in patterns if p['pattern'] == 'Grand Trine']:
        gt_planets = gt['planets']
        for opp in oppositions:
            p1, p2 = opp
            kite_point = None
            trine_planet = None
            if p1 in gt_planets:
                trine_planet = p1
                kite_point = p2
            elif p2 in gt_planets:
                trine_planet = p2
                kite_point = p1
            
            if kite_point and trine_planet:
                other_trine = [p for p in gt_planets if p != trine_planet]
                if has_aspect(kite_point, other_trine[0], sextiles) and has_aspect(kite_point, other_trine[1], sextiles):
                    patterns.append({
                        'pattern': 'Kite',
                        'planets': sorted(gt_planets + [kite_point]),
                        'apex': kite_point,
                        'description': f'Grand Trine with outlet - {kite_point} channels the trine energy productively'
                    })
    
    # MYSTIC RECTANGLE: 2 oppositions + 2 trines + 2 sextiles
    if len(oppositions) >= 2 and len(trines) >= 2 and len(sextiles) >= 2:
        for i, opp1 in enumerate(oppositions):
            for opp2 in oppositions[i+1:]:
                p1, p2 = opp1
                p3, p4 = opp2
                # Check for trines and sextiles forming rectangle
                if ((has_aspect(p1, p3, trines) and has_aspect(p2, p4, trines) and 
                     has_aspect(p1, p4, sextiles) and has_aspect(p2, p3, sextiles)) or
                    (has_aspect(p1, p4, trines) and has_aspect(p2, p3, trines) and 
                     has_aspect(p1, p3, sextiles) and has_aspect(p2, p4, sextiles))):
                    patterns.append({
                        'pattern': 'Mystic Rectangle',
                        'planets': sorted([p1, p2, p3, p4]),
                        'description': 'Balanced tension with creative outlets - practical mysticism'
                    })
    
    # GRAND SEXTILE (Star of David): 6 planets, alternating trines and sextiles
    # Very rare - two interlocking Grand Trines
    all_sextile_planets = set()
    for s in sextiles:
        all_sextile_planets.add(s[0])
        all_sextile_planets.add(s[1])
    
    # CRADLE: 2 planets in opposition, each forms sextile/trine to 2 other planets
    for opp in oppositions:
        p1, p2 = opp
        p1_sextiles = [s[1] if s[0] == p1 else s[0] for s in sextiles if p1 in s]
        p2_sextiles = [s[1] if s[0] == p2 else s[0] for s in sextiles if p2 in s]
        p1_trines = [t[1] if t[0] == p1 else t[0] for t in trines if p1 in t]
        p2_trines = [t[1] if t[0] == p2 else t[0] for t in trines if p2 in t]
        
        # Find planets that complete the cradle
        for sx1 in p1_sextiles:
            for sx2 in p2_sextiles:
                if sx1 != sx2 and has_aspect(sx1, sx2, sextiles):
                    patterns.append({
                        'pattern': 'Cradle',
                        'planets': sorted([p1, p2, sx1, sx2]),
                        'description': 'Supportive container for opposition energy - creative resolution'
                    })
    
    # THOR'S HAMMER (Quadriform): 2 planets square, both sesquiquadrate a third
    sesquiquadrates = [(a['planet1'], a['planet2']) for a in aspects if a['aspect'] == 'sesquiquadrate']
    for sq in squares:
        p1, p2 = sq
        for ss in sesquiquadrates:
            hammer_point = None
            if ss[0] == p1 or ss[1] == p1:
                hammer_point = ss[1] if ss[0] == p1 else ss[0]
            if hammer_point and hammer_point != p2:
                if has_aspect(p2, hammer_point, sesquiquadrates):
                    patterns.append({
                        'pattern': "Thor's Hammer",
                        'planets': sorted([p1, p2, hammer_point]),
                        'apex': hammer_point,
                        'description': f'Intense drive for action - {hammer_point} is the striking point'
                    })
    
    # BOOMERANG: Yod + opposition to apex
    for yod in [p for p in patterns if p['pattern'] == 'Yod']:
        apex = yod['apex']
        for opp in oppositions:
            if apex in opp:
                activation_point = opp[1] if opp[0] == apex else opp[0]
                patterns.append({
                    'pattern': 'Boomerang',
                    'planets': sorted(yod['planets'] + [activation_point]),
                    'apex': apex,
                    'activation_point': activation_point,
                    'description': f'Yod with release point - energy returns transformed through {activation_point}'
                })
    
    return patterns

def calculate_chart_shape(planets):
    """Determine overall chart shape (Bundle, Bowl, Bucket, Locomotive, Splay, Splash, Seesaw)"""
    positions = sorted([p['fullDegree'] for p in planets if p['name'] in ASPECT_PLANETS[:10]])
    
    if len(positions) < 7:
        return None
    
    # Calculate gaps between consecutive planets
    gaps = []
    for i in range(len(positions)):
        next_i = (i + 1) % len(positions)
        gap = positions[next_i] - positions[i]
        if gap < 0:
            gap += 360
        gaps.append(gap)
    
    max_gap = max(gaps)
    spread = 360 - max_gap
    
    # Determine shape
    if spread <= 120:
        shape = 'Bundle'
        description = 'All planets within 120° - concentrated focus, specialist'
    elif spread <= 180:
        shape = 'Bowl'
        description = 'All planets within 180° - self-contained, mission-oriented'
    elif max_gap >= 120:
        # Check for bucket (bowl with one handle planet)
        shape = 'Locomotive'
        description = 'Empty trine (120°) - driven, purposeful, strong momentum'
    else:
        # Count planets in each quadrant
        quadrants = [0, 0, 0, 0]
        for pos in positions:
            q = int(pos / 90)
            quadrants[q] += 1
        
        if max(quadrants) <= 4 and min(quadrants) >= 1:
            shape = 'Splash'
            description = 'Planets spread evenly - versatile, scattered interests'
        else:
            shape = 'Splay'
            description = 'Irregular distribution - individualistic, unique approach'
    
    return {
        'shape': shape,
        'description': description,
        'spread': round(spread, 1),
        'largest_gap': round(max_gap, 1)
    }

def calculate_element_balance(planets):
    """Calculate elemental balance of chart"""
    counts = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    weights = {'Sun': 2, 'Moon': 2, 'Mercury': 1, 'Venus': 1, 'Mars': 1, 
               'Jupiter': 1, 'Saturn': 1, 'Ascendant': 2, 'Midheaven': 1}
    
    for planet in planets:
        if planet['name'] in weights:
            element = ELEMENTS.get(planet['sign'])
            if element:
                counts[element] += weights[planet['name']]
    
    total = sum(counts.values())
    percentages = {k: round(v/total*100, 1) if total > 0 else 0 for k, v in counts.items()}
    
    dominant = max(counts, key=counts.get)
    lacking = min(counts, key=counts.get)
    
    return {
        'counts': counts,
        'percentages': percentages,
        'dominant': dominant,
        'lacking': lacking if counts[lacking] == 0 else None
    }

def calculate_modality_balance(planets):
    """Calculate modality balance of chart"""
    counts = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
    weights = {'Sun': 2, 'Moon': 2, 'Mercury': 1, 'Venus': 1, 'Mars': 1,
               'Jupiter': 1, 'Saturn': 1, 'Ascendant': 2, 'Midheaven': 1}
    
    for planet in planets:
        if planet['name'] in weights:
            modality = MODALITIES.get(planet['sign'])
            if modality:
                counts[modality] += weights[planet['name']]
    
    total = sum(counts.values())
    percentages = {k: round(v/total*100, 1) if total > 0 else 0 for k, v in counts.items()}
    
    dominant = max(counts, key=counts.get)
    
    return {
        'counts': counts,
        'percentages': percentages,
        'dominant': dominant
    }

def calculate_polarity_balance(planets):
    """Calculate polarity (yin/yang) balance"""
    counts = {'Positive': 0, 'Negative': 0}
    weights = {'Sun': 2, 'Moon': 2, 'Mercury': 1, 'Venus': 1, 'Mars': 1,
               'Jupiter': 1, 'Saturn': 1, 'Ascendant': 2, 'Midheaven': 1}
    
    for planet in planets:
        if planet['name'] in weights:
            polarity = POLARITIES.get(planet['sign'])
            if polarity:
                counts[polarity] += weights[planet['name']]
    
    total = sum(counts.values())
    percentages = {k: round(v/total*100, 1) if total > 0 else 0 for k, v in counts.items()}
    
    return {
        'counts': counts,
        'percentages': percentages,
        'dominant': 'Positive (Yang/Masculine)' if counts['Positive'] > counts['Negative'] else 'Negative (Yin/Feminine)'
    }

def calculate_hemisphere_emphasis(planets, asc_deg, mc_deg):
    """Calculate hemisphere emphasis"""
    emphasis = {
        'eastern': 0,  # Houses 10-3 (self-oriented)
        'western': 0,  # Houses 4-9 (other-oriented)
        'northern': 0, # Houses 1-6 (private)
        'southern': 0  # Houses 7-12 (public)
    }
    
    for planet in planets:
        if planet['name'] in ASPECT_PLANETS[:10]:
            lon = planet['fullDegree']
            
            # East/West (relative to Ascendant)
            rel_to_asc = normalize_degree(lon - asc_deg)
            if rel_to_asc < 180:
                emphasis['western'] += 1
            else:
                emphasis['eastern'] += 1
            
            # North/South (relative to MC)
            rel_to_mc = normalize_degree(lon - mc_deg)
            if rel_to_mc < 180:
                emphasis['northern'] += 1
            else:
                emphasis['southern'] += 1
    
    interpretations = []
    if emphasis['eastern'] > emphasis['western'] + 2:
        interpretations.append('Eastern emphasis: Self-directed, initiator')
    elif emphasis['western'] > emphasis['eastern'] + 2:
        interpretations.append('Western emphasis: Relationship-oriented, responsive')
    
    if emphasis['southern'] > emphasis['northern'] + 2:
        interpretations.append('Southern emphasis: Public life, career-focused')
    elif emphasis['northern'] > emphasis['southern'] + 2:
        interpretations.append('Northern emphasis: Private life, inner-focused')
    
    return {
        'counts': emphasis,
        'interpretations': interpretations
    }

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "Swiss Ephemeris API is running",
        "version": "3.0 Platinum",
        "endpoints": {
            "/calculate": "POST - Calculate complete natal chart with all features",
            "/": "GET - This status page"
        },
        "features": [
            "All planets and points",
            "Multiple house systems",
            "All major and minor aspects",
            "Declination aspects (parallel/contraparallel)",
            "Aspect patterns (Grand Trine, T-Square, Yod, Kite, etc.)",
            "Essential dignities",
            "Decans and Terms",
            "Fixed star conjunctions",
            "Chart shape analysis",
            "Element/Modality/Polarity balance",
            "Hemisphere emphasis"
        ],
        "house_systems": HOUSE_SYSTEMS,
        "aspects": list(ASPECTS.keys()),
        "fixed_stars": list(FIXED_STARS.keys()),
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
        house_system = data.get('houseSystem', 'P')
        include_aspects = data.get('includeAspects', True)
        include_patterns = data.get('includePatterns', True)
        include_angle_aspects = data.get('includeAngleAspects', True)
        include_fixed_stars = data.get('includeFixedStars', True)
        include_dignities = data.get('includeDignities', True)
        include_analysis = data.get('includeAnalysis', True)
        
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
                
                sign = get_zodiac_sign(longitude_deg)
                full_degree = normalize_degree(longitude_deg)
                
                planet_data = {
                    'name': name,
                    'fullDegree': full_degree,
                    'degreeInSign': full_degree % 30.0,
                    'sign': sign,
                    'signData': get_sign_data(sign),
                    'latitude': latitude_deg,
                    'distance': distance,
                    'speed': speed,
                    'isRetro': speed < 0
                }
                
                if include_dignities and name in DIGNITIES:
                    planet_data['dignity'] = get_dignity(name, sign)
                    planet_data['decan'] = get_decan(full_degree)
                    planet_data['term'] = get_term(full_degree)
                
                planets.append(planet_data)
            except Exception as e:
                print(f"Could not calculate {name}: {e}")

        # South Node
        north_node = next((p for p in planets if p['name'] == 'North Node'), None)
        if north_node:
            south_node_deg = normalize_degree(north_node['fullDegree'] + 180.0)
            south_sign = get_zodiac_sign(south_node_deg)
            planets.append({
                'name': 'South Node',
                'fullDegree': south_node_deg,
                'degreeInSign': south_node_deg % 30.0,
                'sign': south_sign,
                'signData': get_sign_data(south_sign),
                'latitude': -north_node['latitude'],
                'distance': north_node['distance'],
                'speed': north_node['speed'],
                'isRetro': True
            })

        # Lilith variants
        mean_lilith = next((p for p in planets if p['name'] == 'Mean Lilith'), None)
        if mean_lilith:
            planets.append({
                'name': 'Black Moon Lilith',
                'fullDegree': mean_lilith['fullDegree'],
                'degreeInSign': mean_lilith['degreeInSign'],
                'sign': mean_lilith['sign'],
                'signData': mean_lilith['signData'],
                'latitude': mean_lilith['latitude'],
                'distance': mean_lilith['distance'],
                'speed': mean_lilith['speed'],
                'isRetro': mean_lilith['isRetro']
            })
            
            selena_deg = normalize_degree(mean_lilith['fullDegree'] + 180.0)
            selena_sign = get_zodiac_sign(selena_deg)
            planets.append({
                'name': 'White Moon Selena',
                'fullDegree': selena_deg,
                'degreeInSign': selena_deg % 30.0,
                'sign': selena_sign,
                'signData': get_sign_data(selena_sign),
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

        # Houses
        houses_result = swe.houses_ex(jd, latitude, longitude, house_system.encode())
        cusps = houses_result[0]
        ascmc = houses_result[1]

        asc_deg = normalize_degree(ascmc[0])
        mc_deg = normalize_degree(ascmc[1])
        armc = ascmc[2]
        vertex_deg = normalize_degree(ascmc[3])

        desc_deg = normalize_degree(asc_deg + 180)
        ic_deg = normalize_degree(mc_deg + 180)

        print(f"HOUSES ({HOUSE_SYSTEMS[house_system]}): ASC={asc_deg:.4f}, MC={mc_deg:.4f}")

        # Add angles to planets for aspect calculation
        asc_sign = get_zodiac_sign(asc_deg)
        mc_sign = get_zodiac_sign(mc_deg)
        
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

        # Part of Fortune
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
            
            # Part of Spirit (opposite formula)
            if is_day_chart:
                pos_deg = normalize_degree(asc_deg + sun_lon - moon_lon)
            else:
                pos_deg = normalize_degree(asc_deg + moon_lon - sun_lon)
            
            planets.append({
                'name': 'Part of Spirit',
                'fullDegree': pos_deg,
                'degreeInSign': pos_deg % 30.0,
                'sign': get_zodiac_sign(pos_deg),
                'latitude': 0,
                'distance': 0,
                'speed': 0,
                'isRetro': False
            })

        houses = {
            'system': house_system,
            'system_name': HOUSE_SYSTEMS.get(house_system, 'Unknown'),
            'ascendant': {
                'degree': asc_deg,
                'degreeInSign': asc_deg % 30.0,
                'sign': asc_sign,
                'signData': get_sign_data(asc_sign)
            },
            'midheaven': {
                'degree': mc_deg,
                'degreeInSign': mc_deg % 30.0,
                'sign': mc_sign,
                'signData': get_sign_data(mc_sign)
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
            cusp_sign = get_zodiac_sign(cusp_deg)
            houses['cusps'].append({
                'house': i + 1,
                'degree': cusp_deg,
                'degreeInSign': cusp_deg % 30.0,
                'sign': cusp_sign,
                'signData': get_sign_data(cusp_sign)
            })

        # Calculate aspects
        aspects = []
        declination_aspects = []
        patterns = []
        
        if include_aspects:
            aspects = calculate_all_aspects(planets, include_angle_aspects, asc_deg, mc_deg)
            declination_aspects = calculate_declination_aspects(planets)
            print(f"ASPECTS: Found {len(aspects)} longitude aspects, {len(declination_aspects)} declination aspects")
            
            if include_patterns:
                patterns = detect_aspect_patterns(aspects, planets)
                print(f"PATTERNS: Found {len(patterns)} patterns")

        # Fixed star conjunctions
        fixed_star_conjunctions = []
        if include_fixed_stars:
            fixed_star_conjunctions = check_fixed_star_conjunctions(planets)
            print(f"FIXED STARS: Found {len(fixed_star_conjunctions)} conjunctions")

        # Chart analysis
        analysis = {}
        if include_analysis:
            # Add Ascendant to planets for analysis
            planets_for_analysis = planets + [{'name': 'Ascendant', 'sign': asc_sign, 'fullDegree': asc_deg}]
            planets_for_analysis.append({'name': 'Midheaven', 'sign': mc_sign, 'fullDegree': mc_deg})
            
            analysis = {
                'chartShape': calculate_chart_shape(planets),
                'elementBalance': calculate_element_balance(planets_for_analysis),
                'modalityBalance': calculate_modality_balance(planets_for_analysis),
                'polarityBalance': calculate_polarity_balance(planets_for_analysis),
                'hemisphereEmphasis': calculate_hemisphere_emphasis(planets, asc_deg, mc_deg)
            }

        return jsonify({
            'birthDate': birth_date,
            'birthTime': birth_time,
            'latitude': latitude,
            'longitude': longitude,
            'julianDay': jd,
            'houseSystem': house_system,
            'houseSystemName': HOUSE_SYSTEMS.get(house_system, 'Unknown'),
            'isDayChart': is_day_chart if sun_data and moon_data else None,
            'planets': planets,
            'houses': houses,
            'aspects': aspects,
            'declinationAspects': declination_aspects,
            'aspectPatterns': patterns,
            'fixedStarConjunctions': fixed_star_conjunctions,
            'analysis': analysis,
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

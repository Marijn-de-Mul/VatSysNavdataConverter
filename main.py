# Libraries
import xml.etree.ElementTree as ET
import os
import xml.dom.minidom
import re
from collections import defaultdict
import all_airports
import all_rtes_pts
import vatis_airports
from collections import OrderedDict

# Configuration
lat_range = (-11.00, 6.00)
lon_range = (95.00, 141.00)

# ET Initialization
ET.register_namespace('', "http://www.w3.org/2001/XMLSchema-instance")
ET.register_namespace('xsd', "http://www.w3.org/2001/XMLSchema")

root = ET.Element('{http://www.w3.org/2001/XMLSchema-instance}Airspace')

# Position Formatting
def format_position(lat, lon):
    lat_sign = '+' if lat >= 0 else '-'
    lon_sign = '+' if lon >= 0 else '-'
    lat = abs(lat)
    lon = abs(lon)
    lat_str = f"{lat_sign}{lat:02.4f}".zfill(8)
    lon_str = f"{lon_sign}{lon:03.4f}".zfill(9)
    return f"{lat_str}{lon_str}"

# Remove Consecutive Duplicates
def remove_consecutive_duplicates(lst):
    return [v for i, v in enumerate(lst) if i == 0 or v != lst[i-1]]

def is_in_range(lat, lon, lat_range, lon_range):
    return lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]

# SystemRunways Initialization
system_runways = ET.SubElement(root, 'SystemRunways')

procedure_to_runway = {}

for filename in os.listdir('Navdata/Proc/'):
    if filename.startswith(('WI', 'WA', 'WR')) and filename.endswith('.txt'):
        airport_code = filename[:-4]
        runways = {} 
        sid_exists = False
        airport = None  
        with open(f'Navdata/Proc/{filename}', 'r') as f:
            for line in f:
                data = line.strip().split(',')
                if len(data) < 2:  
                    continue
                if data[0] in ['SID', 'STAR']:
                    if not airport: 
                        airport = ET.SubElement(system_runways, 'Airport', Name=airport_code)
                    if data[2] == 'ALL':
                        for runway_name, runway_element in runways.items():
                            ET.SubElement(runway_element, data[0], Name=data[1])
                            procedure_to_runway[data[1]] = runway_name
                    elif data[2] not in runways:
                        if re.match(r'^\d{1,2}[A-Z]?$', data[2]):
                            runways[data[2]] = ET.SubElement(airport, 'Runway', Name=data[2], DataRunway=data[2])
                    if data[2] in runways: 
                        ET.SubElement(runways[data[2]], data[0], Name=data[1])
                        procedure_to_runway[data[1]] = data[2]  

# SIDSTARs Initialization
sidstars = ET.SubElement(root, 'SIDSTARs')

for filename in os.listdir('Navdata/Proc/'):
    if filename.startswith(('WI', 'WA', 'WR')) and filename.endswith('.txt'):
        airport_code = filename[:-4] 
        airport = system_runways.find(f"./Airport[@Name='{airport_code}']")
        sids = {}
        stars = {}
        current_procedure = None
        current_dict = None
        approaches = {}
        current_approach = None
        current_approach_runway = None
        current_transition = None
        if airport is not None:
            valid_runways = {runway.get('Name') for runway in airport.findall('Runway')}
            valid_procedures = {procedure for procedure, runway in procedure_to_runway.items() if runway in valid_runways}
            if not valid_runways or not valid_procedures: 
                continue
            with open(f'Navdata/Proc/{filename}', 'r') as f:
                for line in f:
                    data = line.strip().split(',')
                    if len(data) < 2:  
                        continue
                    runway_regex = re.compile(r'^\d{1,2}[LRC]?$')

                    if data[0] == 'SID' or data[0] == 'STAR':
                        current_procedure = (airport_code, data[1])
                        current_dict = sids if data[0] == 'SID' else stars

                        if data[2] == 'ALL':
                            current_runway = ','.join(valid_runways)
                            current_dict.setdefault(current_procedure, {})[current_runway] = []
                        else:
                            # Only add the runway if it's a valid runway number
                            if runway_regex.match(data[2]):
                                current_runway = data[2]
                                current_dict.setdefault(current_procedure, {})[current_runway] = []
                    elif data[0] in ['IF', 'TF', 'CF', 'DF', 'FA', 'CA', 'RF', 'AF']:
                        waypoint = {'type': data[0], 'name': data[1]}
                        if current_procedure in current_dict:
                            for runway in current_dict[current_procedure]:
                                current_dict[current_procedure][runway].append(waypoint)
                    if data[0] == 'APPTR':
                        current_approach = data[1]
                        current_approach_runway = data[2]
                        current_transition = data[3]
                        approaches[current_approach] = {'runway': current_approach_runway, 'transitions': defaultdict(list), 'route': []}
                    elif data[0] == 'FINAL' and current_approach:
                        approaches[current_approach]['route'].append({'type': data[0], 'name': data[1]})
                        current_transition = None
                    elif current_approach and current_transition and data[0] in ['TF', 'CA', 'CF', 'DF', 'FA', 'FC', 'FD', 'FM', 'HA', 'HF', 'HM', 'IF', 'RF', 'VA', 'VD', 'VI', 'VM', 'VR', 'HF', 'DF']:
                        if not data[1].isdigit():
                            approaches[current_approach]['transitions'][current_transition].append({'type': data[0], 'name': data[1]})
                    elif current_approach and data[0] in ['TF', 'CA', 'CF', 'DF', 'FA', 'FC', 'FD', 'FM', 'HA', 'HF', 'HM', 'IF', 'RF', 'VA', 'VD', 'VI', 'VM', 'VR', 'HF', 'DF']:
                        if not data[1].isdigit():
                            approaches[current_approach]['route'].append({'type': data[0], 'name': data[1]})

            for (airport_code, procedure_name), runways in sids.items():
                for runway, waypoints in runways.items():
                    procedure = ET.SubElement(sidstars, 'SID', Name=procedure_name, Airport=airport_code, Runways=runway)
                    waypoint_names = [waypoint['name'] for waypoint in waypoints if waypoint['type'] == 'TF']
                    added_transitions = set()
                    for waypoint in waypoints:
                        if waypoint['type'] != 'TF' and waypoint['name'] not in added_transitions and waypoint['name'] != '0':
                            added_transitions.add(waypoint['name'])
                    if len(added_transitions) == 1:
                        waypoint_names.insert(0, next(iter(added_transitions)))
                    if waypoint_names:
                        route_runway = procedure_to_runway.get(procedure_name, 'Unknown')
                        ET.SubElement(procedure, 'Route', Runway=route_runway).text = '/'.join(waypoint_names)
                    for waypoint in waypoints:
                        if waypoint['type'] != 'TF' and waypoint['name'] not in added_transitions and waypoint['name'] != '0':
                            ET.SubElement(procedure, 'Transition', Name=waypoint['name']).text = waypoint['name']
            for (airport_code, procedure_name), runways in stars.items():
                for runway, waypoints in runways.items():
                    runway_list = runway.split(',')
                    procedure = ET.SubElement(sidstars, 'STAR', Name=procedure_name, Airport=airport_code, Runways=','.join(runway_list))
                    waypoint_names = [waypoint['name'] for waypoint in waypoints if waypoint['type'] == 'TF']
                    added_transitions = set()
                    for waypoint in waypoints:
                        if waypoint['type'] != 'TF' and waypoint['name'] not in added_transitions:
                            added_transitions.add(waypoint['name'])
                    if len(added_transitions) == 1:
                        waypoint_names.insert(0, next(iter(added_transitions)))
                    if waypoint_names:
                        for r in runway.split(','):
                            ET.SubElement(procedure, 'Route', Runway=r).text = '/'.join(waypoint_names)
                    for waypoint in waypoints:
                        if waypoint['type'] != 'TF' and waypoint['name'] not in added_transitions:
                            ET.SubElement(procedure, 'Transition', Name=waypoint['name']).text = waypoint['name']
            for approach_name, approach_data in approaches.items():
                approach = ET.SubElement(sidstars, 'Approach', Name=approach_name, Airport=airport_code, Runway=approach_data['runway'])
                for transition_name, waypoints in approach_data['transitions'].items():
                    waypoint_names = [waypoint['name'] for waypoint in waypoints]
                    waypoint_names = remove_consecutive_duplicates(waypoint_names)
                    if waypoint_names:
                        ET.SubElement(approach, 'Transition', Name=transition_name).text = '/'.join(waypoint_names)
                route_names = [waypoint['name'] for waypoint in approach_data['route']]
                route_names = remove_consecutive_duplicates(route_names)
                if route_names and route_names[0] == approach_name:
                    route_names = route_names[1:]
                if route_names:
                    ET.SubElement(approach, 'Route').text = '/'.join(route_names)

# Airports Initialization
airports = ET.SubElement(root, 'Airports')
airport_dict = {}

with open('Navdata/Airports.txt', 'r') as f:
    for line in f:
        data = line.strip().split(',')
        if len(data) < 5:  
            continue
        record_type, code, *_ = data
        if record_type == 'A':
            airport_code = code
            _, _, _, lat, lon, elevation, *_ = data
            try:
                float_lat = float(lat)
                float_lon = float(lon)
            except ValueError:
                continue
            if airport_code.startswith(('WI', 'WA', 'WP', 'WR')):  
                position = format_position(float_lat, float_lon)
                airport = ET.SubElement(airports, 'Airport', ICAO=airport_code, Position=position, Elevation=elevation)
                airport_dict[airport_code] = airport
        elif record_type == 'R':
            _, runway_name, _, _, _, _, _, _, lat, lon, *_ = data
            try:
                float_lat = float(lat)
                float_lon = float(lon)
            except ValueError:
                continue
            position = format_position(float_lat, float_lon)
            airport = airport_dict.get(airport_code) 
            if airport is not None:
                ET.SubElement(airport, 'Runway', Name=runway_name, Position=format_position(float_lat, float_lon))
                
# Airways Initialization
airways_dict = {}

with open('Navdata/ATS.txt', 'r') as f:
    airway_name = None
    waypoints = []
    for line in f:
        data = line.strip().split(',')
        if not data:
            continue
        if data[0] == 'A':
            if airway_name is not None and waypoints:
                if all(is_in_range(lat, lon, lat_range, lon_range) for wp, (lat, lon) in waypoints):
                    airways_dict[airway_name] = [wp for wp, _ in waypoints]
                waypoints = []
            airway_name = data[1]
        elif data[0] == 'S' and airway_name is not None:
            waypoint1 = data[1]
            lat1 = float(data[2])
            lon1 = float(data[3])
            waypoint2 = data[4]
            lat2 = float(data[5])
            lon2 = float(data[6])
            waypoints.append((waypoint1, (lat1, lon1)))
            waypoints.append((waypoint2, (lat2, lon2)))
    if airway_name is not None and waypoints:
        if all(is_in_range(lat, lon, lat_range, lon_range) for wp, (lat, lon) in waypoints):
            airways_dict[airway_name] = [wp for wp, _ in waypoints]

airways = ET.SubElement(root, 'Airways')
for airway_name, waypoints in airways_dict.items():
    unique_waypoints = list(OrderedDict.fromkeys(waypoints))  
    if unique_waypoints:  
        airway = ET.SubElement(airways, 'Airway', Name=airway_name)
        airway.text = '/'.join(unique_waypoints)

# Intersections Initialization
intersections = ET.SubElement(root, 'Intersections')

with open('Navdata/Waypoints.txt', 'r') as f:
    for line in f:
        data = line.strip().split(',')
        if not data:
            continue
        name = data[0]
        lat = float(data[1])
        lon = float(data[2])
        if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
            point = ET.SubElement(intersections, 'Point', Name=name, Type="Fix")
            point.text = format_position(lat, lon)

navaids_set = set()

with open('Navdata/Navaids.txt', 'r') as f:
    for line in f:
        data = line.strip().split(',')
        if not data:
            continue
        name = data[0]
        frequency = data[2]
        lat = float(data[6])
        lon = float(data[7])
        if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
            if (name, frequency, lat, lon) not in navaids_set:
                point = ET.SubElement(intersections, 'Point', Name=name, Type="Navaid", NavaidType="None", Frequency=frequency)
                point.text = format_position(lat, lon)
                navaids_set.add((name, frequency, lat, lon))  

# XML Fomatting
def format_xml(element):
    dom = xml.dom.minidom.parseString(ET.tostring(element, 'utf-8')) 
    pretty_xml = dom.toprettyxml()  
    return pretty_xml

os.makedirs("Output", exist_ok=True)

pretty_xml = format_xml(root)
with open('Output/Airspace.xml', 'w') as f:
    f.write(pretty_xml)

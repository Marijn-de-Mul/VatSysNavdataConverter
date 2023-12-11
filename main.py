import xml.etree.ElementTree as ET
import os
import xml.dom.minidom
import re

def format_xml(element):
    dom = xml.dom.minidom.parseString(ET.tostring(element, 'utf-8')) 
    pretty_xml = dom.toprettyxml()  
    return pretty_xml

ET.register_namespace('', "http://www.w3.org/2001/XMLSchema-instance")
ET.register_namespace('xsd', "http://www.w3.org/2001/XMLSchema")

root = ET.Element('{http://www.w3.org/2001/XMLSchema-instance}Airspace')

system_runways = ET.SubElement(root, 'SystemRunways')

lat_range = (-13, +7)
lon_range = (+91, +142)

procedure_to_runway = {}

for filename in os.listdir('Navdata/Proc/'):
    if filename.startswith(('WI', 'WA')) and filename.endswith('.txt'):
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
                    if data[2] not in runways:
                        if re.match(r'^\d{1,2}[A-Z]?$', data[2]):
                            runways[data[2]] = ET.SubElement(airport, 'Runway', Name=data[2], DataRunway=data[2])
                    if data[2] in runways: 
                        # if airport_code == 'WIII' and data[2] in ['06', '24']:
                        #     continue
                        ET.SubElement(runways[data[2]], data[0], Name=data[1])
                        procedure_to_runway[data[1]] = data[2]  

sidstars = ET.SubElement(root, 'SIDSTARs')

for filename in os.listdir('Navdata/Proc/'):
    if filename.startswith(('WI', 'WA')) and filename.endswith('.txt'):
        airport_code = filename[:-4] 
        airport = system_runways.find(f"./Airport[@Name='{airport_code}']")
        sids = {}
        stars = {}
        current_procedure = None
        current_dict = None
        if airport is not None:
            valid_runways = {runway.get('Name') for runway in airport.findall('Runway')}
            valid_procedures = {procedure for procedure, runway in procedure_to_runway.items() if runway in valid_runways}
            if not valid_runways or not valid_procedures:  # Skip this airport if there are no valid runways or procedures
                continue
            with open(f'Navdata/Proc/{filename}', 'r') as f:
                for line in f:
                    data = line.strip().split(',')
                    if len(data) < 2:  
                        continue
                    if data[0] == 'SID':
                        current_procedure = data[1]
                        current_dict = sids
                        current_dict[current_procedure] = []
                    elif data[0] == 'STAR':
                        current_procedure = data[1]
                        current_dict = stars
                        current_dict[current_procedure] = []
                    elif current_procedure and data[0] in ['TF', 'CA', 'CF', 'DF', 'FA', 'FC', 'FD', 'FM', 'HA', 'HF', 'HM', 'IF', 'RF', 'VA', 'VD', 'VI', 'VM', 'VR', 'HF', 'DF']:
                        if not data[1].isdigit():
                            current_dict[current_procedure].append({'type': data[0], 'name': data[1]})

            for procedure_name, waypoints in sids.items():
                if procedure_name in valid_procedures:
                    runways = procedure_to_runway.get(procedure_name, 'Unknown')
                    if runways == 'ALL':
                        runways = ','.join(valid_runways)
                    procedure = ET.SubElement(sidstars, 'SID', Name=procedure_name, Airport=airport_code, Runways=runways)
                    waypoint_names = [waypoint['name'] for waypoint in waypoints if waypoint['type'] == 'TF']
                    if waypoint_names:
                        ET.SubElement(procedure, 'Route', Runway=procedure_to_runway.get(procedure_name, 'Unknown')).text = '/'.join(waypoint_names)
                    added_transitions = set()
                    for waypoint in waypoints:
                        if waypoint['type'] != 'TF' and waypoint['name'] not in added_transitions:
                            ET.SubElement(procedure, 'Transition', Name=waypoint['name']).text = waypoint['name']
                            added_transitions.add(waypoint['name'])
            for procedure_name, waypoints in stars.items():
                if procedure_name in valid_procedures:
                    runways = procedure_to_runway.get(procedure_name, 'Unknown')
                    if 'ALL' in runways:
                        runways = ','.join(valid_runways)
                    else:
                        runways = ','.join(runway for runway in runways.split(',') if runway != 'ALL')
                    procedure = ET.SubElement(sidstars, 'STAR', Name=procedure_name, Airport=airport_code, Runways=runways)
                    waypoint_names = [waypoint['name'] for waypoint in waypoints if waypoint['type'] == 'TF']
                    if waypoint_names:
                        route_runway = procedure_to_runway.get(procedure_name, 'Unknown')
                        if 'ALL' in route_runway:
                            route_runway = ','.join(valid_runways)
                        else:
                            route_runway = ','.join(runway for runway in route_runway.split(',') if runway != 'ALL')
                        ET.SubElement(procedure, 'Route', Runway=route_runway).text = '/'.join(waypoint_names)
                    added_transitions = set()
                    for waypoint in waypoints:
                        if waypoint['type'] != 'TF' and waypoint['name'] not in added_transitions:
                            ET.SubElement(procedure, 'Transition', Name=waypoint['name']).text = waypoint['name']
                            added_transitions.add(waypoint['name'])

def format_position(lat, lon):
    lat_sign = '+' if lat >= 0 else '-'
    lon_sign = '+' if lon >= 0 else '-'
    lat = abs(lat)
    lon = abs(lon)
    lat_str = f"{lat_sign}{lat:02.4f}".zfill(8)
    lon_str = f"{lon_sign}{lon:03.4f}".zfill(9)
    return f"{lat_str}{lon_str}"

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
            if airport_code.startswith(('WI', 'WA')):  
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
                if airway_name in airways_dict and len(airways_dict[airway_name]) < len(waypoints):
                    airways_dict[airway_name] = waypoints
                elif airway_name not in airways_dict:
                    airways_dict[airway_name] = waypoints
                waypoints = []
            airway_name = data[1]
        elif data[0] == 'S' and airway_name is not None:
            waypoint = data[1]
            next_waypoint = data[4]
            lat = float(data[2])
            lon = float(data[3])
            if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
                waypoints.append(waypoint)
            lat_next = float(data[5])
            lon_next = float(data[6])
            if lat_range[0] <= lat_next <= lat_range[1] and lon_range[0] <= lon_next <= lon_range[1]:
                waypoints.append(next_waypoint)
    if airway_name is not None and waypoints:
        if airway_name in airways_dict and len(airways_dict[airway_name]) < len(waypoints):
            airways_dict[airway_name] = waypoints
        elif airway_name not in airways_dict:
            airways_dict[airway_name] = waypoints

airways = ET.SubElement(root, 'Airways')
for airway_name, waypoints in airways_dict.items():
    airway = ET.SubElement(airways, 'Airway', Name=airway_name)
    airway.text = '/'.join(waypoints)

intersections = ET.SubElement(root, 'Intersections')

with open('Navdata/Waypoints.txt', 'r') as f:
    for line in f:
        data = line.strip().split(',')
        if not data:
            continue
        name = data[0]
        lat = float(data[1])
        lon = float(data[2])
        lat_range = (-13, +7) 
        lon_range = (+91, +142) 
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
        lat_range = (-13, +7) 
        lon_range = (+91, +142) 
        if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:
            if (name, frequency, lat, lon) not in navaids_set:
                point = ET.SubElement(intersections, 'Point', Name=name, Type="Navaid", NavaidType="None", Frequency=frequency)
                point.text = format_position(lat, lon)
                navaids_set.add((name, frequency, lat, lon))  

pretty_xml = format_xml(root)
with open('Airspace.xml', 'w') as f:
    f.write(pretty_xml)

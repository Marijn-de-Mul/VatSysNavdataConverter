import xml.etree.ElementTree as ET
import os
import xml.dom.minidom

def format_xml(element):
    dom = xml.dom.minidom.parseString(ET.tostring(element, 'utf-8')) 
    pretty_xml = dom.toprettyxml()  
    return pretty_xml

ET.register_namespace('', "http://www.w3.org/2001/XMLSchema-instance")
ET.register_namespace('xsd', "http://www.w3.org/2001/XMLSchema")

root = ET.Element('{http://www.w3.org/2001/XMLSchema-instance}Airspace')

system_runways = ET.SubElement(root, 'SystemRunways')

procedure_to_runway = {}

for filename in os.listdir('Navdata/Proc/'):
    if filename.startswith(('WI', 'WA')) and filename.endswith('.txt'):
        airport_code = filename[:-4]
        airport = ET.SubElement(system_runways, 'Airport', Name=airport_code)
        runways = {} 
        with open(f'Navdata/Proc/{filename}', 'r') as f:
            for line in f:
                data = line.strip().split(',')
                if len(data) < 2:  
                    continue
                if data[0] == 'SID':
                    if data[2] not in runways:
                        runways[data[2]] = ET.SubElement(airport, 'Runway', Name=data[2], DataRunway=data[2])
                    ET.SubElement(runways[data[2]], 'SID', Name=data[1])
                    procedure_to_runway[data[1]] = data[2] 
                elif data[0] == 'STAR':
                    if data[2] not in runways:
                        runways[data[2]] = ET.SubElement(airport, 'Runway', Name=data[2], DataRunway=data[2])
                    ET.SubElement(runways[data[2]], 'STAR', Name=data[1])
                    procedure_to_runway[data[1]] = data[2]  

sidstars = ET.SubElement(root, 'SIDSTARs')

for filename in os.listdir('Navdata/Proc/'):
    if filename.startswith(('WI', 'WA')) and filename.endswith('.txt'):
        airport_code = filename[:-4] 
        sids = {}
        stars = {}
        approaches = {}
        current_procedure = None
        current_dict = None
        airport = system_runways.find(f"./Airport[@Name='{airport_code}']")
        if airport is not None:
            valid_runways = {runway.get('Name') for runway in airport.findall('Runway')}
            valid_procedures = {procedure for procedure, runway in procedure_to_runway.items() if runway in valid_runways}
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
                    elif data[0] == 'APP':
                        current_procedure = data[1]
                        current_dict = approaches
                        current_dict[current_procedure] = []
                    elif current_procedure and data[0] in ['TF', 'CA', 'CF', 'DF', 'FA', 'FC', 'FD', 'FM', 'HA', 'HF', 'HM', 'IF', 'RF', 'VA', 'VD', 'VI', 'VM', 'VR', 'HF', 'DF']:
                        if not data[1].isdigit():
                            current_dict[current_procedure].append({'type': data[0], 'name': data[1]})

            for procedure_name, waypoints in sids.items():
                    if procedure_name in valid_procedures:
                        procedure = ET.SubElement(sidstars, 'SID', Name=procedure_name, Airport=airport_code, Runways=procedure_to_runway.get(procedure_name, 'Unknown'))
                        waypoint_names = [waypoint['name'] for waypoint in waypoints if waypoint['type'] == 'TF']
                        if waypoint_names:
                            ET.SubElement(procedure, 'Route', Runway=procedure_to_runway.get(procedure_name, 'Unknown')).text = '/'.join(waypoint_names)
                        added_transitions = set()
                        for waypoint in waypoints:
                            if waypoint['type'] != 'TF' and waypoint['name'] not in added_transitions:
                                ET.SubElement(procedure, 'Transition', Name=waypoint['name']).text = waypoint['name']
                                added_transitions.add(waypoint['name'])
            # for procedure_name, waypoints in stars.items():
            #         if procedure_name in valid_procedures:
            #             procedure = ET.SubElement(sidstars, 'STAR', Name=procedure_name, Airport=airport_code, Runways=procedure_to_runway.get(procedure_name, 'Unknown'))
            #             waypoint_names = [waypoint['name'] for waypoint in waypoints if waypoint['type'] == 'TF']
            #             if waypoint_names:
            #                 ET.SubElement(procedure, 'Route', Runway=procedure_to_runway.get(procedure_name, 'Unknown')).text = '/'.join(waypoint_names)
            #             added_transitions = set()
            #             for waypoint in waypoints:
            #                 if waypoint['type'] != 'TF' and waypoint['name'] not in added_transitions:
            #                     ET.SubElement(procedure, 'Transition', Name=waypoint['name']).text = waypoint['name']
            #                     added_transitions.add(waypoint['name']) 
            # for procedure_name, waypoints in approaches.items():
            #     procedure = ET.SubElement(sidstars, 'Approach', Name=procedure_name, Airport=airport_code, Runway=procedure_to_runway.get(procedure_name, 'Unknown'))
            #     for waypoint in waypoints:
            #         if waypoint['type'] == 'TF':
            #             ET.SubElement(procedure, 'Route').text = waypoint['name']
            #         else:
            #             ET.SubElement(procedure, 'Transition', Name=waypoint['name']).text = waypoint['name']

pretty_xml = format_xml(root)
with open('Airspace.xml', 'w') as f:
    f.write(pretty_xml)
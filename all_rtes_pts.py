import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import re
from shapely.geometry import Point, Polygon
import copy

def copy_map_elements(map_elements):
    return copy.deepcopy(map_elements)

def create_map_element(Type, Name, Priority, Center, CustomColourName):
    map_element = ET.Element("Map", {"Type": Type, "Name": Name, "Priority": str(Priority), "Center": Center, "CustomColourName": CustomColourName})

    return map_element

def create_line_element(Name, Pattern, CustomColourName, waypoints):
    line_element = ET.Element("Line", {"Name": Name, "Pattern": Pattern, "CustomColourName": CustomColourName})

    waypoints_text = f"{waypoints[0][0]}.{Name}.{waypoints[-1][0]}"
    line_element.text = waypoints_text

    return line_element

def create_point_element(waypoint):
    point_element = ET.Element("Point")
    point_element.text = waypoint  

    return point_element

def create_symbol_element(waypoints, airway_waypoints):
    symbol_element = ET.Element("Symbol", {"Type": "SolidTriangle"})

    for waypoint in waypoints:
        if waypoint[0] in airway_waypoints:
            point_element = create_point_element(waypoint)
            symbol_element.append(point_element)

    return symbol_element

def get_map_type(airway_name):
    first_letter = airway_name[0]
    if first_letter in ['T', 'W', 'Z']:
        return f"AIRWAY_{first_letter}"
    else:
        return "AIRWAY_INTL"

jakarta_polygon_coords = [
    (6.000000, 92.000000),
    (6.000000, 97.500000),
    (1.650000, 102.166667),
    (1.619952, 102.161432),
    (1.359425, 102.140931),
    (1.098927, 102.161432),
    (0.844865, 102.222429),
    (0.603488, 102.322430),
    (0.380732, 102.458980),
    (0.182079, 102.628729),
    (0.012414, 102.827506),
    (-0.124086, 103.050421),
    (-0.224060, 103.291987),
    (-0.566667, 104.216667),
    (-0.483000, 104.576000),
    (-0.283333, 104.866667),
    (0.000000, 104.766667),
    (0.000000, 105.166667),
    (-0.833333, 106.000000),
    (0.000000, 108.000000),
    (0.000000, 109.000000),
    (0.250000, 109.000000),
    (0.767222, 108.683056),
    (1.692500, 109.007222),
    (2.115278, 109.496111),
    (2.123333, 109.715833),
    (1.761111, 109.729445),
    (1.552500, 109.845000),
    (1.310833, 110.067222),
    (1.069167, 110.317222),
    (0.959445, 110.515000),
    (1.019722, 110.820000),
    (1.124167, 111.188056),
    (1.080278, 111.803056),
    (1.434445, 112.160278),
    (1.656667, 112.613333),
    (1.588056, 113.080278),
    (1.486667, 113.102222),
    (1.216667, 113.583333),
    (-3.000000, 110.383333),
    (-8.333333, 110.383333),
    (-12.000000, 114.500000),
    (-12.000000, 107.000000),
    (-2.000000, 92.000000),
    (6.000000, 92.000000)
]

ujung_polygon_coords = [
    (1.216667, 113.583333),
    (4.555278, 115.514722),
    (4.642778, 117.331111),
    (4.000000, 118.000000),
    (4.000000, 132.533333),
    (3.500000, 133.000000),
    (3.500000, 141.000000),
    (-6.320556, 141.000000),
    (-6.892778, 141.018333),
    (-9.616667, 141.033333),
    (-9.833333, 141.000000),
    (-9.833333, 139.666667),
    (-7.000000, 135.000000),
    (-9.333333, 126.833333),
    (-12.000000, 123.333333),
    (-12.000000, 114.500000),
    (-8.333333, 110.383333),
    (-3.000000, 110.383333),
    (1.216667, 113.583333)
]

jakarta_polygon = Polygon(jakarta_polygon_coords)
ujung_polygon = Polygon(ujung_polygon_coords)

def process_fir(fir_name, polygon, line_pattern):
    min_latitude = min(p[0] for p in polygon.exterior.coords)
    max_latitude = max(p[0] for p in polygon.exterior.coords)
    min_longitude = min(p[1] for p in polygon.exterior.coords)
    max_longitude = max(p[1] for p in polygon.exterior.coords)

    center_latitude = (min_latitude + max_latitude) / 2
    center_longitude = (min_longitude + max_longitude) / 2

    center_latitude_parts = str(abs(center_latitude)).split('.')
    center_longitude_parts = str(abs(center_longitude)).split('.')

    center_latitude_str = f"{'-' if center_latitude < 0 else ''}{center_latitude_parts[0].zfill(2)}.{center_latitude_parts[1]}"
    center_longitude_str = f"{'-' if center_longitude < 0 else ''}{center_longitude_parts[0].zfill(3)}.{center_longitude_parts[1]}"

    center = f"{center_latitude_str}+{center_longitude_str}"

    root = ET.Element("Maps")

    map_elements = {
        "AIRWAY_INTL": create_map_element("System", "AIRWAY_INTL", 1, center, "SubtleGrey"),
        "AIRWAY_T": create_map_element("System", "AIRWAY_T", 1, center, "SubtleGrey"),
        "AIRWAY_W": create_map_element("System", "AIRWAY_W", 1, center, "SubtleGrey"),
        "AIRWAY_Z": create_map_element("System", "AIRWAY_Z", 1, center, "SubtleGrey"),
    }

    map_symbols = {
        "AIRWAY_INTL": ET.Element("Symbol", {"Type": "SolidTriangle"}),
        "AIRWAY_T": ET.Element("Symbol", {"Type": "SolidTriangle"}),
        "AIRWAY_W": ET.Element("Symbol", {"Type": "SolidTriangle"}),
        "AIRWAY_Z": ET.Element("Symbol", {"Type": "SolidTriangle"}),
    }

    symbol_elements = {
        "AIRWAY_INTL": ET.Element("Symbol", {"Type": "SolidTriangle"}),
        "AIRWAY_T": ET.Element("Symbol", {"Type": "SolidTriangle"}),
        "AIRWAY_W": ET.Element("Symbol", {"Type": "SolidTriangle"}),
        "AIRWAY_Z": ET.Element("Symbol", {"Type": "SolidTriangle"}),
    }

    for map_element in map_elements.values():
        root.append(map_element)

    airways_set = set()
    airway_waypoints = {}

    with open("Navdata/ATS.txt", "r") as file:
        waypoints = []
        airway_name = None
        for line in file:
            components = line.strip().split(",")

            if components[0] == "A":
                if components[1] in airways_set:
                    continue

                airways_set.add(components[1])

                if waypoints:
                    map_type = get_map_type(airway_name)
                    line_element = create_line_element(airway_name, line_pattern, "SubtleGrey", waypoints)
                    map_elements[map_type].append(line_element)
                    waypoints = []

                airway_name = components[1]
                airway_waypoints[airway_name] = []

            elif components[0] == "S":
                point1 = (components[1], float(components[2]), float(components[3]))
                point2 = (components[4], float(components[5]), float(components[6]))

                buffer_distance = 0.05 
                buffered_polygon = polygon.buffer(buffer_distance)

                if buffered_polygon.covers(Point(point1[1], point1[2])) and buffered_polygon.covers(Point(point2[1], point2[2])):
                    if point1 not in waypoints:
                        waypoints.append(point1)
                        airway_waypoints[airway_name].append(point1[0]) 
                    if point2 not in waypoints:
                        waypoints.append(point2)
                        airway_waypoints[airway_name].append(point2[0])  

        if waypoints:
            map_type = get_map_type(airway_name)
            line_element = create_line_element(airway_name, line_pattern, "SubtleGrey", waypoints)
            map_elements[map_type].append(line_element)
            waypoints = []

    symbol_element = ET.Element("Symbol", {"Type": "SolidTriangle"})  

    for airway_name, waypoints in airway_waypoints.items():
        if waypoints:  
            map_type = get_map_type(airway_name)  
            for waypoint in waypoints:
                point_element = create_point_element(waypoint)  
                map_symbols[map_type].append(point_element) 

    for map_type, symbol_element in map_symbols.items():
        map_elements[map_type].append(symbol_element)
    
    copied_map_elements = copy_map_elements(map_elements)

    for map_type, map_element in copied_map_elements.items():
        map_element.attrib["Type"] = "System"
        map_element.attrib["Name"] = f"{map_type}_NAMES"
        if "CustomColourName" in map_element.attrib:
            del map_element.attrib["CustomColourName"]

        # Remove all <Line> tags and their content
        for line_element in map_element.findall('Line'):
            map_element.remove(line_element)

        # Get all Symbol elements in map_element
        symbol_elements = map_element.findall('Symbol')

        for symbol_element in symbol_elements:
            if symbol_element.tag == 'Symbol':
                label_attrib = symbol_element.attrib.copy()
                if 'Type' in label_attrib:
                    del label_attrib['Type']
                label_element = ET.Element('Label', label_attrib)
                label_element[:] = symbol_element[:]
                index = symbol_elements.index(symbol_element)
                map_element.insert(index, label_element)
                map_element.remove(symbol_element)

    for map_element in copied_map_elements.values():
        root.append(map_element)

    tree = ET.ElementTree(root)

    xml_str = ET.tostring(root, 'utf-8')

    dom = xml.dom.minidom.parseString(xml_str)

    pretty_xml_str = dom.toprettyxml(indent="  ")

    os.makedirs(f"Output/{fir_name}", exist_ok=True)

    with open(f"Output/{fir_name}/ALL_RTES_PTS.xml", "w") as files:
        files.write(pretty_xml_str)

process_fir("Jakarta", jakarta_polygon, "Dotted")
process_fir("Ujung", ujung_polygon, "Dashed")
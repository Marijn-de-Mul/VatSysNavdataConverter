import xml.etree.ElementTree as ET
import xml.dom.minidom
import os

# Function to create a new XML tree
def create_tree():
    root = ET.Element("Maps")

    map_elem = ET.SubElement(root, "Map")
    map_elem.set("Type", "System2")
    map_elem.set("Name", "ALL_AIRPORTS")
    map_elem.set("Priority", "2")
    map_elem.set("Center", "-03+116.5")

    label_elem = ET.SubElement(map_elem, "Label")
    label_elem.set("HasLeader", "true")
    label_elem.set("LabelOrientation", "NW")

    return root, label_elem

# Create two separate XML trees
jakarta_root, jakarta_label = create_tree()
ujung_root, ujung_label = create_tree()

for filename in os.listdir("Navdata/Proc"):
    icao_code = os.path.splitext(filename)[0]
    if icao_code.startswith("WI"):
        point_elem = ET.SubElement(jakarta_label, "Point")
        point_elem.text = icao_code
    elif icao_code.startswith("WA"):
        point_elem = ET.SubElement(ujung_label, "Point")
        point_elem.text = icao_code

# Function to write an XML tree to a file
def write_tree(root, filename):
    tree = ET.ElementTree(root)

    xml_string = ET.tostring(root, encoding="utf-8")

    dom = xml.dom.minidom.parseString(xml_string)
    pretty_xml_string = dom.toprettyxml()

    with open(filename, "w") as f:
        f.write(pretty_xml_string)

os.makedirs("Output/Jakarta", exist_ok=True)
os.makedirs("Output/Ujung", exist_ok=True)

# Write each XML tree to a separate file
write_tree(jakarta_root, "Output/Jakarta/ALL_AIRPORTS.xml")
write_tree(ujung_root, "Output/Ujung/ALL_AIRPORTS.xml")
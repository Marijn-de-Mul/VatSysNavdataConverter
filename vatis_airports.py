import os
import yaml

if not os.path.exists('Output'):
    os.makedirs('Output')

if os.path.exists('Output/airports.yaml'):
    os.remove('Output/airports.yaml')

with open('Navdata/Airports.txt', 'r') as f:
    lines = f.readlines()

indonesian_airports = [line for line in lines if line.startswith(('A,WI', 'A,WA'))]

data = []
for airport in indonesian_airports:
    parts = airport.split(',')
    if parts[1].isalpha():
        data.append({
            'ID': parts[1],
            'Name': parts[2],
            'Lat': float(parts[3]),
            'Lon': float(parts[4])
        })

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

yaml.add_representer(dict, dict_representer)

with open('Output/airports.yaml', 'w') as f:
    yaml.dump(data, f)
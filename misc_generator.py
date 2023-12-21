with open('Navdata/Airports.txt', 'r') as file:
    icao_codes_WI = []
    icao_codes_WA = []

    for line in file:
        parts = line.split(',')

        if parts[0] == 'A' and parts[1].startswith('WI') and parts[1].isalpha():
            icao_codes_WI.append(parts[1])
        if parts[0] == 'A' and parts[1].startswith('WA') and parts[1].isalpha():
            icao_codes_WA.append(parts[1])
        if parts[0] == 'A' and parts[1].startswith('WP') and parts[1].isalpha():
            icao_codes_WA.append(parts[1])
        if parts[0] == 'A' and parts[1].startswith('WR') and parts[1].isalpha():
            icao_codes_WA.append(parts[1])

icao_codes_WI_str = ', '.join(icao_codes_WI)
icao_codes_WA_str = ', '.join(icao_codes_WA)

print(icao_codes_WI_str)
print(icao_codes_WA_str)
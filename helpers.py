import typing
import json

# average_price_calculator returns the average price of the top five flights
def average_price(prices: List[Any]) -> float:
    average_price = 0
    count = 0
    for i in range(min(5, len(prices))):
      # Remove the $ sign from the front
        price = prices[i].text[1:].replace(',', '')
        if not price:
            print("Warning: No price found for a data point, Skipping")
            continue
        price = float(price)
        # TO-DO
        # Noticed Kayak occasionally returns prices that are too high (e.g. air taxi)
        if price <= 10000:
            count += 1
            average_price += price
    if not count:
        return -1
    return average_price / count

# returns a dictionary of the nearest airports to the start city
def nearest_cities(cities: typing.List[str], start_city_iata: str) -> typing.Dict[str, float]:
    with open('distances.json', 'r') as f:
        iata_cities_distances = json.load(f)
    final_map = {}
    for city in cities:
        # Extract the distance from the string
        # should be in the form xx (miles | km): city, country (IATA / ICAO) airport_name
        temp_distance = city.split()[0]
        if not temp_distance or temp_distance.isalpha(): 
            continue
        distance = float(temp_distance)
        # Convert km to miles if necessary
        if 'km' in city:
            distance *= 0.621371
        iata = city[-7:-4]
        # Skip if the city is the start city or the distance is not within the expected range
        if iata == start_city_iata or distance < 55 or distance > 300:
            continue
        final_map[iata] = distance
    iata_cities_distances[start_city_iata] = final_map
    with open('distances.json', 'w') as f:
        json.dump(iata_cities_distances, f, indent=2)
    return final_map

def cleanup():
  print('CLEANING')
  with open('city_routes.json') as f:
    print("Loading city_routes.json")
    city_routes_alliance: typing.Dict[str, typing.Dict[str, typing.List[str]]] = json.load(f)
    f.close()
  for city in city_routes_alliance:
    for alliance in city_routes_alliance[city]:
      city_routes_alliance[city][alliance] = list(set(city_routes_alliance[city][alliance]))
  with open('city_routes.json', 'w') as f:
    json.dump(city_routes_alliance, f, indent=2)
    f.close()
  print('CLEANED')

## TO-DO: Write test cases

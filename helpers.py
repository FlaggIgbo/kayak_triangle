import typing
import json

# average_price_calculator returns the average price of the top three flights
def average_price_calculator(prices: typing.List[typing.Any]) -> float:
  if len(prices) == 0:
    raise Exception('no flights returned')
  average_price = 0
  counter = 0
  for i in range(min(5, len(prices))):
    # remove the dollar sign from the front
    text_without_dollar_sign = prices[i].text[1:].replace(',', '')
    if len(text_without_dollar_sign) == 0:
      print("Warning: No price found for a data point, Skipping")
      continue
    text_to_number = float(text_without_dollar_sign)
    if text_to_number > 10000:
      ## TO-DO
      # Noticed Kayak occasionally returns prices that are too high (e.g. air taxi)
      print("Warning: Price is too high, Skipping")
      continue
    counter += 1
    average_price += text_to_number
    print("Price found")
  if counter == 0:
    return -1
  average_price /= counter
  return average_price

# returns a dictionary of the nearest airports to the start city
def nearest_cities(cities: typing.List[str], start_city_iata: str) -> typing.Dict[str, float]:
    with open('distances.json', 'r') as f:
        iata_cities_distances = json.load(f)
    final_map = {}
    for city in cities:
        # Extract the distance from the string
        distance = float(city.split()[0])
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
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
  with open('distances.json') as f:
    print("Loading distances.json")
    iata_cities_distances_airports: typing.Dict[str, typing.Dict[str, float]] = json.load(f)
    f.close()
  final_map = {}
  for city in cities:
    ## should be in the form xx (miles | km): city, country (IATA / ICAO) airport_name
    # TO-DO: use regex
    numbers = '0123456789'
    distance = ''
    for char in city:
        if char in numbers:
            distance += char
        else:
          break
    if not distance:
      continue
    final_distance = float(distance)
    # find the : character
    index_of_colon = city.find(':')
    if index_of_colon == -1:
      continue
    # The distance should be in miles
    if "km" in city[:index_of_colon]:
      final_distance *= 0.621371
    if city[index_of_colon + 2: index_of_colon + 5].upper() == start_city_iata:
      continue
    # find the first bracket
    index_of_first_bracket = city.find('(')
    iata = city[index_of_first_bracket + 1: index_of_first_bracket + 4]
    # Using NYC and LON data to estimate distances in miles
    ## TO-DO: This logic could be improved by using iata_cities data
    if final_distance < 55 or final_distance > 300:
      continue
    final_map[iata] = final_distance
  if start_city_iata not in iata_cities_distances_airports:
    print("Adding to database")
    iata_cities_distances_airports[start_city_iata] = final_map
    with open('distances.json', 'w') as f:
      json.dump(iata_cities_distances_airports, f, indent=2)
      f.close()
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
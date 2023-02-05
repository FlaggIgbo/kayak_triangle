import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import argparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import typing
import json
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from helpers import average_price_calculator, cleanup, nearest_cities

# Pull JSON files as dictionaries
with open('iata_cities.json') as f:
  print("Loading iata_cities.json")
  iata_cities_to_airports: typing.Dict[str, typing.List[str]] = json.load(f)
  f.close()

with open('distances.json') as f:
  print("Loading distances.json")
  iata_cities_distances_airports: typing.Dict[str, typing.Dict[str, float]] = json.load(f)
  f.close()

with open('city_routes.json') as f:
  print("Loading city_routes.json")
  city_routes_alliance: typing.Dict[str, typing.Dict[str, typing.List[str]]] = json.load(f)
  f.close()

class FlightSearch:
  def __init__(self, start: str, end: str, start_date: str, end_date: str, cabin: typing.Union[str, None], alliance: str):
    self.start = start.upper() 
    self.end = end.upper()
    self.start_date = start_date
    self.end_date = end_date
    self.cabin = cabin if cabin else 'economy'
    self.alliance = alliance if alliance else 'None'

# Parse inputs from command line
parser = argparse.ArgumentParser(description='Extend round trip travel by adding one city')
## TO-DO: accept cities (e.g. Chicago) as a valid input and convert to IATA code
## TO-DO: right now you only use airport codes, not city codes
parser.add_argument('--start', type=str, help='start airport as IATA code', required=True)
parser.add_argument('--end', type=str, help='end airport as IATA code', required=True)
parser.add_argument('--start-date', type=str, help='start date as YYYY-MM-DD', required=True)
## TO-DO: allow for one-way trips
parser.add_argument('--end-date', type=str, help='end date as YYYY-MM-DD', required=True)
parser.add_argument('--cabin', type=str, help='class of travel, should be economy or business or first')
parser.add_argument('--alliance', type=str, help='airline alliance, should be ONE_WORLD, SKY_TEAM, STAR_ALLIANCE or ALL.')
arguments = parser.parse_args()
# We use Kayak here because it is easier to search for flight prices using the URL
def kayak_search_price(args: FlightSearch) -> float:
  final_url = 'https://www.kayak.com/flights/' + args.start + '-' + args.end + '/' + args.start_date + '/' + args.end_date + '?sort=bestflight_a'
  # If the user specified an alliance, search using that. If all, use all alliances. Otherwise, search all alliance airlines (better for price estimates)
  if args.alliance in ('ONE_WORLD', 'SKY_TEAM', 'STAR_ALLIANCE'):
      final_url += '&fs=alliance=' + args.alliance
  elif args.alliance == 'ALL':
      final_url += '&fs=alliance=ONE_WORLD,SKY_TEAM,STAR_ALLIANCE'
  # The chromedriver version should match the version of chrome you have installed, otherwise you will get an error
  driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
  driver.get(final_url)
  # We do this because sometimes kayak will display an ad
  print("Pulling prices for round_trip flight")
  try:
    time.sleep(5)
    prices = WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), '$')]")))
  except:
    print("\nCouldn't pull any prices \n")
    var = input("Enter the price manually. Enter 0 if there is no price: ")
    return float(var)
  average_price = average_price_calculator(prices)
  print("Average price for round-trip from " + args.start + " to " + args.end + " is $" + str(average_price))
  driver.quit()
  return average_price

# take the IATA code and find the nearest airports
def city_search(city_iata: str) -> typing.List[str]:
    if city_iata in iata_cities_distances_airports:
        print("Pulling from distance.json database")
        return iata_cities_distances_airports[city_iata]
    
    driver = webdriver.Chrome(service=webdriver.Service(ChromeDriverManager().install()))
    driver.get(f'https://www.travelmath.com/nearest-airport/{city_iata}')
    print(f"Finding nearest airports to {city_iata}")

    try:
        cities = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'li'))
        )
        cities_cleaned = [i.text for i in cities]
    except:
        print(f"Warning: Couldn't find nearest cities to {city_iata}")
        cities_cleaned = []
    finally:
        driver.quit()
        print("Done")
        
    return cities_cleaned

# find cheap cities to fly to from the end city
def explore_end_city(args: FlightSearch) -> typing.List[str]:
    # Check if the city and alliance data exists in city_routes_alliance
    if args.end in city_routes_alliance and args.alliance in city_routes_alliance[args.end]:
        print(f"Pulling from city_routes.json database for {args.end}")
        return city_routes_alliance[args.end][args.alliance]
    
    city_list = iata_cities_to_airports.get(args.end, [args.end])
    cities = []
    for end_city in city_list:
        if end_city in city_routes_alliance and args.alliance in city_routes_alliance[end_city]:
            print(f"Pulling from city_routes.json database for {end_city}")
            cities += city_routes_alliance[end_city][args.alliance]
        else:
            url = f'https://www.flightsfrom.com/api/airport/{end_city}?durationFrom=00.00&durationTo=190.00&priceFrom=0.00&priceTo=120.00&from={args.end}&classes={args.cabin}'
            try:
                response = requests.get(url).json()
                airport_routes = response['response']['routes']
            except:
                print(f"Problem pulling airport data for {end_city}")
                continue

            cities += [route['iata_to'] if isinstance(route, dict) else route[index]['iata_to'] for route in airport_routes]
            print(f"Airport Data pulled for {end_city}")

    final_list = list(set(cities))
    city_routes_alliance.setdefault(args.end, {})
    city_routes_alliance[args.end][args.alliance] = final_list

    with open('city_routes.json', 'w') as f:
        json.dump(city_routes_alliance, f, indent=2)

    return final_list

def direct_routes(airport_iata_from: str, airport_iata_to_list: typing.Dict[str, float], alliance: str) -> typing.Dict[str, bool]:
  return_dict = {k: False for k in airport_iata_to_list}
  if airport_iata_from in city_routes_alliance and alliance in city_routes_alliance[airport_iata_from]:
    print("Pulling from city_routes.json database for " + airport_iata_from + " \n")
    temp_list = city_routes_alliance[airport_iata_from][alliance]
    for element in temp_list:
      if element in return_dict:
        return_dict[element] = True
    ## Don't return yet, we need to check for longer direct routes
  if airport_iata_from in iata_cities_to_airports:
    print("Multiple Cities for " + airport_iata_from + " \n")
    cities = iata_cities_to_airports[airport_iata_from]
  else:
    cities = [airport_iata_from]
  for iata in cities:
    url = 'https://www.flightsfrom.com/api/airport/' + iata
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)
    text_json = json.loads(driver.find_element(By.TAG_NAME, 'body').text)
    try:
      airport_routes = text_json['response']['routes']
    except:
      print("Problem pulling airport data for " + iata + " \n")
      continue
    for element in airport_routes:
      print('looking at ' + element['iata_to'])
      if element['iata_to'] in airport_iata_to_list:
        if alliance == 'ALL':
          for airlines in element['airlineroutes']:
            if airlines['airline']['is_oneworld'] == '1' or airlines['airline']['is_skyteam'] == '1' or airlines['airline']['is_staralliance'] == '1':
              return_dict[element['iata_to']] = True
        elif alliance == 'ONE_WORLD':
          for airlines in element['airlineroutes']:
            if airlines['airline']['is_oneworld'] == '1':
              return_dict[element['iata_to']] = True
        elif alliance == 'SKY_TEAM':
          for airlines in element['airlineroutes']:
            if airlines['airline']['is_skyteam'] == '1':
              return_dict[element['iata_to']] = True
        elif alliance == 'STAR_ALLIANCE':
          for airlines in element['airlineroutes']:
            if airlines['airline']['is_staralliance'] == '1':
              return_dict[element['iata_to']] = True
        else:
          return_dict[element['iata_to']] = True
  print("Adding to city_routes.json database")
  temp_list = [k for k in return_dict if return_dict[k]]
  return return_dict

# find price for multi-city itinerary
# TO-DO: better way to speed this up? maybe using the flightsfrom.com API?
def kayak_search_price_multi_city(args: FlightSearch, cities: typing.Dict[str, float]) -> typing.List[float]:
  all_prices: typing.List[float] = []
  ## figure out which cities have direct flights to the start city
  new_cities = direct_routes(args.start, cities, args.alliance)
  
  # Initialize the webdriver once, outside of the loop
  # The chromedriver version should match the version of chrome you have installed, otherwise you will get an error
  driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
  
  for c, value in new_cities.items():
    if not value:
      all_prices.append(-1)
      continue
    final_url = 'https://www.kayak.com/flights/' + args.start + '-' + args.end + '/' + args.start_date + '/' + c + '-' + args.start + '/' + args.end_date + '/?sort=bestflight_a'
    # If the user specified an alliance, search using that. If all, use all alliances. Otherwise, search all alliance airlines (better for price estimates)
    if args.alliance in ('ONE_WORLD', 'SKY_TEAM', 'STAR_ALLIANCE'):
        final_url += '&fs=alliance=' + args.alliance
    elif args.alliance == 'ALL':
        final_url += '&fs=alliance=ONE_WORLD,SKY_TEAM,STAR_ALLIANCE'
    ## TO-DO: account for time of day?
    # final_url += ';takeoff=__1800,2300'
    driver.get(final_url)
    # We do this because sometimes kayak will display an ad
    print("Pulling prices for multi-city flight")
    try:
      time.sleep(5)
      prices = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), '$')]")))
    except:
      print("\nCouldn't pull any prices for multi-city flight \n")
      var = input("Enter the price manually. Enter -1 if there is no price: ")
      all_prices.append(float(var))
      continue
    average_price = average_price_calculator(prices)
    all_prices.append(average_price)
  # Quit the webdriver once, outside of the loop
  driver.quit()
  return all_prices

# First search the price for a return
args = FlightSearch(arguments.start, arguments.end, arguments.start_date, arguments.end_date, arguments.cabin, arguments.alliance)
avg_price = kayak_search_price(args)
# Now generate list of possible cities
# First generate by distance
## TO-DO: Too complex to consider ACB, let's just focus on the BCA case
cities_B = city_search(args.end)
cities_from_B = nearest_cities(cities_B, args.end)
# Now find places you can fly to from A and B
## TO-DO: To avoid complexity, let's focus on the BCA case where those travels occur on the same day
cities_fly_B = explore_end_city(args)
prices_B = kayak_search_price_multi_city(args, cities_from_B)
# display as dictionary
dict_cities_B = dict(zip(cities_from_B.keys(), prices_B))
prices_B_fly = kayak_search_price_multi_city(args, cities_fly_B)
dict_cities_B_fly = dict(zip(cities_fly_B, prices_B_fly))
## Need to cleanup in case
cleanup()
print('PLACES YOU CAN GET TO BY CAR OR TRAIN THEN FLY COMPARED TO AVERAGE')
new_dict_cities_B = {}
for key, value in dict_cities_B.items():
  if value == -1 or max(value - avg_price, 0) > 200:
    continue
  new_dict_cities_B[key] = max(value - avg_price, 0)
print(new_dict_cities_B)
print('PLACES YOU CAN FLY TO THEN FLY OUT OF COMPARED TO AVERAGE')
new_dict_cities_B_fly = {}
for key, value in dict_cities_B_fly.items():
  if value == -1 or max(value-avg_price, 0) > 200:
    continue
  new_dict_cities_B_fly[key] = max(value - avg_price, 0)
print(new_dict_cities_B_fly)

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import argparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import typing
import json

from helpers import average_price_calculator, nearest_cities

class FlightSearch:
  def __init__(self, start: str, end: str, start_date: str, end_date: str, cabin: typing.Union[str, None], alliance: typing.Union[str, None]):
    self.start = start.upper() 
    self.end = end.upper()
    self.start_date = start_date
    self.end_date = end_date
    self.cabin = cabin if cabin else 'economy'
    self.alliance = alliance if alliance else ''

# Parse inputs from command line
parser = argparse.ArgumentParser(description='Extend round trip travel by adding one city')
## TO-DO: accept cities (e.g. Chicago) as a valid input and convert to IATA code
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
  driver = webdriver.Chrome('/chromedriver')
  driver.get(final_url)
  # We do this because sometimes kayak will display an ad
  print("Pulling prices")
  try:
    time.sleep(5)
    prices = WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), '$')]")))
  except:
    raise Exception("Couldn't pull any prices")
  average_price = average_price_calculator(prices)
  print("Average price for round-trip from " + args.start + " to " + args.end + " is $" + str(average_price))
  driver.quit()
  return average_price

# take the IATA code and find the nearest airports
# TO-DO: Use a mongo DB to store information that has already been searched before
def city_search(city_iata: str) -> typing.List[str]:
  driver = webdriver.Chrome('/chromedriver')
  driver.get('https://www.travelmath.com/nearest-airport/' + city_iata)
  print("Finding nearest cities to " + city_iata)
  try:
    cities = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'li')))
  except:
    print("Warning: Couldn't find nearest cities")
    return []
  cities_cleaned = [i.text for i in cities]
  driver.quit()
  print("Done")
  return cities_cleaned

# TO-DO
def kayak_search_price_explore_start(args: FlightSearch) -> float:
  pass

# find cheap cities to fly to from the end city
def kayak_search_price_explore_end(args: FlightSearch) -> typing.List[str]:
  url = 'https://www.flightsfrom.com/api/airport/' + args.end + '?durationFrom=00.00&durationTo=190.00&priceFrom=0.00&priceTo=120.00&timeFrom=0&timeTo=600&from=' + args.end + '&classes=' + args.cabin
  driver = webdriver.Chrome('/chromedriver')
  driver.get(url)
  text_json = json.loads(driver.find_element(By.TAG_NAME, 'body').text)
  cities = []
  try:
    airport_routes = text_json['response']['routes']
  except:
      print("Problem pulling airport data")
      return cities
  cities = []
  for index in airport_routes:
    try:
      cities.append(airport_routes[index]['iata_to'])
    except:
      print("Problem pulling airport data")
      return cities
  print("Airport Data pulled")
  return cities

# find price for multi-city itinerary
# TO-DO: better way to speed this up? maybe using the flightsfrom.com API?
def kayak_search_price_multi_city(args: FlightSearch, cities: typing.List[str]) -> typing.List[float]:
  all_prices = []
  for c in cities:
    final_url = 'https://www.kayak.com/flights/' + args.start + '-' + args.end + '/' + args.start_date + '/' + c + '-' + args.start + '/' + args.end_date + '/?sort=bestflight_a'
    # If the user specified an alliance, search using that. If all, use all alliances. Otherwise, search all alliance airlines (better for price estimates)
    if args.alliance in ('ONE_WORLD', 'SKY_TEAM', 'STAR_ALLIANCE'):
        final_url += '&fs=alliance=' + args.alliance
    elif args.alliance == 'ALL':
        final_url += '&fs=alliance=ONE_WORLD,SKY_TEAM,STAR_ALLIANCE'
    final_url += ';takeoff=__1800,2300'
    # The chromedriver version should match the version of chrome you have installed, otherwise you will get an error
    driver = webdriver.Chrome('/chromedriver')
    driver.get(final_url)
    # We do this because sometimes kayak will display an ad
    print("Pulling prices")
    try:
      time.sleep(5)
      prices = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), '$')]")))
    except:
      print("Couldn't pull any prices")
      all_prices.append(-1)
      continue
    average_price = average_price_calculator(prices)
    all_prices.append(average_price)
    driver.quit()
  return all_prices

# First search the price for a return
args = FlightSearch(arguments.start, arguments.end, arguments.start_date, arguments.end_date, arguments.cabin, arguments.alliance)
avg_price = kayak_search_price(args)
# Now generate list of possible cities
# First generate by distance
## TO-DO: Too complex, let's just focus on the BCA case
# cities_A = city_search(args.start)
# cities_from_A = nearest_cities(cities_A, args.start)
cities_B = city_search(args.end)
cities_from_B = nearest_cities(cities_B, args.end)
# Now find places you can fly to from A and B
## TO-DO: To avoid complexity, let's focus on the BCA case where those travels occur on the same day
# cities_fly_A = kayak_search_price_explore_start(args)
cities_fly_B = kayak_search_price_explore_end(args)
prices_B = kayak_search_price_multi_city(args, cities_from_B)
# display as dictionary
dict_cities_B = dict(zip(cities_from_B.keys(), prices_B))
print('PLACES YOU CAN DRIVE TO THEN FLY COMPARED TO AVERAGE')
print('Note: If the value is -1, then the price could not be found')
for key, value in dict_cities_B.items():
  if value == -1:
    continue
  dict_cities_B[key] = max(value - avg_price, 0)
prices_B_fly = kayak_search_price_multi_city(args, cities_fly_B)
dict_cities_B_fly = dict(zip(cities_fly_B, prices_B_fly))
print('PLACES YOU CAN FLY TO THEN FLY OUT OF COMPARED TO AVERAGE')
print('Note: If the value is -1, then the price could not be found')
for key, value in dict_cities_B_fly.items():
  if value == -1:
    continue
  dict_cities_B_fly[key] = max(value - avg_price, 0)
print(dict_cities_B_fly)
# TO-DO: Now compare to round trip to see how much extra it would be
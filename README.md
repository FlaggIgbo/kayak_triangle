# Kayak - Triangle Travel

flights.py is a python script that finds a third city to fly through and explore for your itinerary.

## Explanation

A round trip flight can be represented as a graph with nodes A and B, and edges A->B and B->A. The goal is to find a city (a new node C) which can be visited by either from B or A (so the new edges could be A->B B->C C->A or A->C C->B B->A). The total price of transportation for all three edges should be less than $x more than the original round trip flight (TO-DO).

## Requirements
(as of December 2022)
- Python3
- Chrome v108
- OS X (not sure if this works on windows)

### Websites
- Kayak
- TravelMath
- FlightsFrom

## Usage

First you need to install the required imports:
```
pip install -r requirements.txt
```
Here is an example command line input: 
```
python3 flights.py --start NYC --start-date 2023-02-02 --end SFO --end-date 2023-03-03 --alliance ALL
```
Debugging information will print out, but the main outputs will looks something like this:
```
PLACES YOU CAN DRIVE TO THEN FLY
Note: If the value is -1, then the price could not be found
{'SMF': 321.4, 'FAT': 339.4, 'SCK': -1, 'STS': -1}

PLACES YOU CAN FLY TO THEN FLY OUT OF
Note: If the value is -1, then the price could not be found
{'Denver': 448.6, 'San Diego': -1, 'Boise': -1, 'Santa Ana': 350.0}
```

## Troubleshooting

- Stalling when pulling prices. Selenium can be a hit or miss, so just press command + C to skip over that step to the next
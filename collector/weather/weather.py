

import requests
import pprint
import math

weather_stations = [
    {'id': 6949212, 'name': 'Ham'},
    {'id': 2639389, 'name': 'Richmond'},
    {'id': 2657697, 'name': 'Acton'},
    {'id': 2634549, 'name': 'Wembley'},
    {'id': 8063096, 'name': 'Earlsfield'},
    {'id': 2634812, 'name': 'Wandsworth'},
    {'id': 2647567, 'name': 'Hammersmith'},
    {'id': 2638043, 'name': 'Shepherds Bush'},
    {'id': 6690581, 'name': 'Belsize Park'},
    {'id': 3333215, 'name': 'Wandsworth'},
    {'id': 6690602, 'name': 'Battersea'},
    {'id': 2653265, 'name': 'Chelsea'},
    {'id': 2648110, 'name': 'Greater London'},
    {'id': 2640692, 'name': 'Paddington'},
    {'id': 3333138, 'name': 'Camden'},
    {'id': 6692466, 'name': 'Brixton Hill'},
    {'id': 6690877, 'name': 'Brixton'},
    {'id': 6545250, 'name': 'Lambeth'},
    {'id': 2634341, 'name': 'City of Westminster'},
    {'id': 6690574, 'name': 'Clerkenwell'},
    {'id': 3333156, 'name': 'Islington'},
    {'id': 6693937, 'name': 'Crystal Palace'},
    {'id': 3345438, 'name': 'Camberwell'},
    {'id': 2643744, 'name': 'City of London'},
    {'id': 2637221, 'name': 'Spitalfields'},
    {'id': 6690989, 'name': 'Bethnal Green'},
    {'id': 2647694, 'name': 'Hackney'},
    {'id': 2653516, 'name': 'Catford'},
    {'id': 3333166, 'name': 'Lewisham'},
    {'id': 2640091, 'name': 'Poplar'},
    {'id': 3333147, 'name': 'Greenwich'},
    {'id': 2645726, 'name': 'Kidbrooke'},
    {'id': 2633583, 'name': 'Woolwich'},
    {'id': 2641639, 'name': 'Newham'},
    {'id': 2650430, 'name': 'East Ham'},
]


def get_weather_stations():
    """
    Get all weather stations within a grid of GPS coordinates. The
    """

    grid_ur = {'lat': 51.546695, 'lon': 0.025578}
    grid_ll = {'lat': 51.443542, 'lon': -0.272805}
    grid_lat_step = 7
    grid_lon_step = 6
    app_id = '<insert Open Weather API ID>'

    latitudes = [grid_ll['lat'] + (grid_ur['lat'] - grid_ll['lat']) / grid_lat_step * i
                 for i in range(0, grid_lat_step + 1)]
    longitudes = [grid_ll['lon'] + (grid_ur['lon'] - grid_ll['lon']) / grid_lon_step * i
                 for i in range(0, grid_lon_step + 1)]

    stations = {}
    for lon in longitudes:
        for lat in latitudes:
            url = f'https://api.openweathermap.org/data/2.5/weather?' \
                  f'lat={lat}&lon={lon}&APPID={app_id}'
            print(url)
            response = requests.get(url)
            data = response.json()
            if data['id'] not in stations.keys():
                stations[data['id']] = data['name']
    for station_id in stations.keys():
        print(f"{{'id': {station_id}, 'name': '{stations[station_id]}'}},")


# get weather data for all station IDs
app_id = '<insert Open Weather API ID>'
batch_size = 20
for step in range(0, math.ceil(len(weather_stations)/batch_size)):
    start_batch = step * batch_size
    end_batch = min(start_batch + batch_size, len(weather_stations))
    station_ids = str([entry['id']
                       for entry in weather_stations[start_batch:end_batch]])[1:-1].replace(' ', '')
    url = f'https://api.openweathermap.org/data/2.5/group?id={station_ids}&units=metric&APPID={app_id}'
    print(url)
    response = requests.get(url)
    data = response.json()
    pprint.pprint(data)

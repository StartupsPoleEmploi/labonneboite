# Isochronous timing

## Introduction

Isochronous timing refers to a sequence of events occurring regularly or at equal time intervals. In our project, it adds the possibility to **search firms by time travel** instead of distance. For example, a user may ask "What are the firms located at 30 minutes by car from Metz city center".

### Search area

Searching by distance returns a disc-shaped list of points, as it uses a radius from a certain location.

![](readme_images/timetravelplatform_radius.png?raw=true)
*Generated using [Travel Time Platform](https://www.traveltimeplatform.com/)*

On the contrary, searching by isochrone generates several polygon-shaped lists of points. *Why?* Because the unit of measure is no longer a **distance** as the crow flies, which is linear, but the **time** required to go from point A to point B. This time does not depend on the distance but on many **parameters**: transport mode, infrastructures (Is a firm easily reached by bus? Is there a road around and how fast can one drive on it? etc.), public transport interconnections, ... This "breaks up" space and leads to a fragmented action zone: a set of several polygons.

![](readme_images/timetravelplatform_isochrone.png?raw=true)
*Reachable zones using public transport in Paris in 30 minutes from city center.*


### APIs and requirements

Our project allows searching by two transport modes: car or public transports. To get isochrone polygons given a certain location, we call two APIs:

- car: [IGN](https://geoservices.ign.fr/documentation/geoservices/isochrones.html)
- public transports: [Navitia](http://doc.navitia.io/#journeys)

Requirements:
- Huey: asynchronous task queue used to cache isochrones and durations.
- A Redis server: used as a backend for Huey. Recommended in production. Default to local cache.
- Elastic Search to find firms in a set of polygons.
- Flash-assets to compile Javascript

## Constants

### In case of emergency

A global switch is available in the settings: `ENABLE_ISOCHRONES`. If turned off, it hides buttons on the front end so that the users are no longer able to filter by time travel.

`labonneboite/templates/search/results/content.html`

```
<div id="distance-duration-switch"
  class="{{ "hidden" if not enable_isochrones else "" }}"
  data-switch-value-selected="{{ "duration" if duration_filter_enabled else "distance"}}">
  ...
</div>
```


### Other useful settings

`labonneboite/conf/common`

```
# Services called to get isochrone polygons.
# Available backends: dummy, ign, navitia
TRAVEL_VENDOR_BACKENDS = {
    'isochrone': {
        'car': 'ign',
        'public': 'navitia',
    },
    'durations': {
        'car': 'ign',
        'public': 'navitia',
    },
}

# Redis cache (unnecessary if we use local travel cache)
# Useful in production but you need to setup a Redis server!
REDIS_SENTINELS = [] # e.g: [('localhost', 26379)]
REDIS_SERVICE_NAME = 'redis-lbb' # same as declared by sentinel config file
# The following are used only if REDIS_SENTINELS is empty. (useful in
# development where there is no sentinel)
REDIS_HOST = 'localhost'
REDIS_PORT = 6389

# Set this to False to simply trash async tasks (useful in tests)
PROCESS_ASYNC_TASKS = True

# 'dummy, 'local' or 'redis'
TRAVEL_CACHE = 'local'

# IGN credentials for fetching travel durations and isochrones
IGN_CREDENTIALS = {
    'key': '',
    'username': '',
    'password': ''
}
NAVITIA_API_TOKEN = 'setme'
```

Constants can be found here: `labonneboite/common/maps/constants`. They define, amongst other things, 3 durations and 2 travel modes:

```
ISOCHRONE_DURATIONS_MINUTES = (15, 30, 45)
DEFAULT_TRAVEL_MODE = CAR_MODE
```

`ISOCHRONE_DURATIONS_MINUTES` is also used in the search form to display available durations.


## High level flow



## Detailed flow


## Cache


## Debugging locally


## Tests


## Available routes


## Requirements
requests
huey
redis
elasticsearch and this app search blueprint
Flash-assets to compile JS scripts
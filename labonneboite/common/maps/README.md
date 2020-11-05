# Isochronous timing

Content:
- [Introduction](#introduction)
- [Settings](#settings)
- [High Level Flow](#high-level-flow)
- [Available backends to interact with APIs](#available-backends-to-interact-with-apis)
- [Asynchronous tasks](#asynchronous-tasks)
- [Endpoints](#endpoints)
- [Tests](#tests)
- [Production monitoring](#monitoring)


## Introduction

Isochronous timing refers to a sequence of events occurring regularly or at equal time intervals. In our project, it adds the possibility to **search companies by commuting time** instead of distance. For example, a user may ask "Find me offices located at 30 minutes by car from Metz city center".


### Search area

Searching by distance returns a **disc-shaped list of points**, as it uses a **radius** from a given location.

![](readme_images/traveltimeplatform_radius.png?raw=true)
*Generated using [Travel Time Platform](https://www.traveltimeplatform.com/)*

On the contrary, searching by commute time generates several polygon-shaped lists of points. *Why?* Because the unit of measure is no longer a **distance** as the crow flies, which is linear, but **time** required to go from point A to point B. It does not depend on the distance but on many **parameters**: transport mode, infrastructures (Is an office easily reached by bus? Is there a road around and how fast can one drive on it? etc.), public transport interconnections, ... This "breaks up" space and leads to a fragmented action zone: a set of several polygons.

![](readme_images/traveltimeplatform_isochrone.png?raw=true)
*Reachable zones using public transport in Paris in 30 minutes from city center.*


### APIs and requirements

Our project allows searching by two transport modes: car or public transports. To get isochrone polygons given a certain location, we call two APIs:

- car: [IGN](https://geoservices.ign.fr/documentation/geoservices/isochrones.html)
- public transports: [Navitia](http://doc.navitia.io/#journeys)


Requirements:

- **Elastic Search** search by polygon feature is used to find offices.


## Settings


### In case of emergency

A global switch is available in the settings: `ENABLE_ISOCHRONES`. If turned off, it hides buttons on the front end so that the users are no longer able to filter by commute time.

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
# Available backends: dummy, ign, navitia, navitia_mock, ign_mock
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

# Credentials for fetching travel durations and isochrones
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
TRAVEL_MODES = (
    PUBLIC_MODE,
    CAR_MODE,
)
```

:information_source: `ISOCHRONE_DURATIONS_MINUTES` is also used in the search form to display available durations.


## High level flow

### User interface

User is on the search page (`url_for('search.entreprises')`: `/entreprises`). He wants to filter search results by time instead of distance. He clicks on "min" (for "minutes") and then selects the transport mode of its choice:
- :bus: "_Transports en commun_" (public transports)
- :blue_car: **"_Voiture_"** (car) => default

He can also select a duration:
- less than 15 minutes,
- **less than 30 minutes**, => default
- less than 45 minutes,
- more than 45 minutes.

Each time he selects an option (transport mode or duration), a new search is made. Results are displayed on a map and detailed underneath on a list.

### Under the hood

Global view:

1. Use Elastic Search to filter offices located inside polygons.
1. Display filtered results to the user.
1. Show commuting time for each office in JS.

#### Use Elastic Search

Elastic Search understands pretty well geometric data, including polygons. We just have to pass it to the Elastic Search query. This is made in two steps:

`labonneboite/web/search/views.py`

```
@searchBlueprint.route('/entreprises')
def entreprises():
    # Convert request arguments to fetcher parameters
    parameters = get_parameters(request.args)

    # Fetch offices and alternatives
    # Other filters are hidden in this documentation for readability purposes.
    fetcher = search_util.HiddenMarketFetcher(
        longitude, latitude,
        travel_mode=parameters['travel_mode'],
        duration=parameters['duration'],
        # ...
    )
```


`labonneboite/common/search.py`

```
def build_json_body_elastic_search(...):
    # ...
    # Add a filter in Elastic Search
    if duration is not None:
        isochrone = travel.isochrone((latitude, longitude), duration, mode=travel_mode)
        if isochrone:
            for polygon in isochrone:
                should_filters.append({
                    "geo_polygon": {
                        "locations": {
                            "points": [[p[1], p[0]] for p in polygon]
                        }
                    }
                })
```

#### Display filtered results to the user

Once results are ready in the `search.entreprises` view, two templates can be shown:
- if request is an AJAX call: `search/results_content.html`
- if not: `search/results.html`


`labonneboite/web/search/views.py`

```
@searchBlueprint.route('/entreprises')
def entreprises():
    # Render different template if it's an ajax call
    template = 'search/results.html' if not request.is_xhr else 'search/results_content.html'
```

Both are located here: `labonneboite/templates/`

:information_source: This is not specific to isochrone requests. It may be useful to refresh results using Ajax calls, for example when a user moves the map with the "refresh results when I move the map" check box enabled.


#### Show commute time for each office

![](readme_images/commuting_time.png)

Commute time is not part of former templates, instead it's generated by this script: `labonneboite/web/static/js/results.js`.

```
(function ($) {

  $(document).on('lbbready', function () {
    // ...
    updateTravelDurations();
  }
}
```

:information_source: Durations are retrieved 5 by 5 to avoid timeouts from upstream servers. In theory, the tinier a batch is, the less timeouts we should receive. But tests in production proved that it's not really the case in our hard reality.

## Available backends to interact with APIs

We use APIs to compute commute duration and to get isochrones. They are located in this folder: `labonneboite/common/maps/vendors`.

- **ign** (default): sends HTTP requests to the IGN API. Requires credentials (see [settings](#settings) section).
- **navitia** (default): sends HTTP requests to the Navitia API. Requires credentials (see [settings](#settings) section).
- **dummy**: a backend that returns None.
- **ign_mock**: based on real HTTP requests to the IGN API and stored as JSON files, this backend returns registered data matching the Metz area. Useful for tests or in development mode.
- **navitia_mock**: based on real HTTP requests to the Navitia API and stored as JSON files, this backend returns registered data matching the Metz area. Useful for tests or in development mode.

:warning: **In development mode**, it is only possible to use the **isochrone features** for the Metz area in search results page (ie searching offices by travel mode or by duration). **Commute time** in office details is **not displayed** as we would need too many JSON files to match all the offices available in our development database. Nevertheless, it is available for tests.


_configuration_file_
```
# Available backends: dummy, ign, navitia, ign_mock, navitia_mock
# isochrone: to filter search results.
# durations: to display commute time in offices details.
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
```

## Endpoints

Two routes are available. They are defined here: `labonneboite/web/maps/views.py`.


### `maps.durations` view (`/maps/durations`)

**POST only**

Returns commute durations from an origin to multiple destinations.

Used in `labonneboite/web/static/js/results.js` to retrieve durations in AJAX.


Arguments:
- `travel_mode`: string ('public' or 'car'),
- `origin`: tuple of floats ("{latitude},{longitude}". eg; 49.119146,6.176026),
- `destinations`: list of coordinates (eg: ["49.1062,6.22691","49.1112,6.22369"]).


### **`maps.isochrone` view** (`/maps/isochrone`)

Displays a full-width map with isochrone polygons.

Useful for debugging or pre-filling data in production.

Arguments:
- `tr` (transport mode),
- `dur` (duration)
- `zipcode` (zipcode).

Example with `/maps/isochrone?dur=15&tr=public&zipcode=75010`:

![](readme_images/isochrone_map.png)


## Tests

Unit and functional tests are available:
- [Functional (high-level) tests using Selenium](/labonneboite/tests/selenium).
- [Unit tests](/tests/app/maps)

## Monitoring

Useful links
- https://labonneboite.pole-emploi.fr/health/ign/duration
- https://labonneboite.pole-emploi.fr/health/ign/isochrone
- Global IGN dashboard: https://stats.uptimerobot.com/28xBxu6Q9

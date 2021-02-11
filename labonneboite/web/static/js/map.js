/* jshint esversion: 6 */
function createMap(element, center, zoom) {
  var mapEl = new mapboxgl.Map({
    container: element,
    style: 'https://maps.labonneboite.pole-emploi.fr/styles/osm-bright/style.json',
    attributionControl: false,
    center: center,
    zoom: zoom
  });
  mapEl.addControl(new mapboxgl.NavigationControl(), 'top-left');
  mapEl.addControl(new mapboxgl.AttributionControl({ compact: true }));
  mapEl.scrollZoom.disable();
  return mapEl;
}

(function($) {
  var center = null;
  var zoom = null;
  var autoRefreshActivated = false;

  function initResultsMap() {
    "use strict";
    var $map = $('#lbb-result-map');
    var $latitude = $("#lat");
    var $longitude = $("#lon");
    if (!$map.length) {
      return;
    }

    var minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
    var companies = [];
    $(".lbb-result").each(function() {
      var companyName = $(this).find('input[name="company-name"]').val();
      var lat = $(this).find('input[name="company-latitude"]').val();
      var lng = $(this).find('input[name="company-longitude"]').val();
      var siret = $(this).find('input[name="company-siret"]').val();
      var description = $(this).find('.company-naf-text').html();
      var link = "<a class='map-marker' href='#company-" + siret + "'>" + companyName + "</a><br>" + description;
      companies.push({
        coords: [lng, lat],
        link: link
      });

      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    });

    $map.on("click", "a.map-marker", function(e) {
        var href = this.attributes.href.value;
        // Toggle company details on click on link
        $(href).find(".js-result-toggle-details").click();
    });

    // Focus either on the companies or the requested coordinates
    var bounds = null;
    if (center === null || zoom === null) {
      zoom = zoom || 13;
      if (companies.length == 0) {
        center = [$longitude.val(), $latitude.val()];
      }
      else {
        center = [0.5*(minLng + maxLng), 0.5*(minLat + maxLat)];
        if (companies.length > 1) {
          bounds = [
            [minLng, minLat],
            [maxLng, maxLat]
          ];
        }
      }
    }

    try {
      var map = createMap($map[0], center, zoom);
      map.on("load", function() {
        if (bounds) {
          // We cannot fit to bounds in constructor: this feature was added in
          // v0.51.0 of mapbox-gl.js while we are using v0.43.0.
          // https://github.com/mapbox/mapbox-gl-js/pull/5518/files
          map.fitBounds(bounds, { duration: 0 }, { initialZoom: true });
        }
        companies.forEach(function(company) {
          var popup = new mapboxgl.Popup()
            .setHTML(company.link);
          var marker = new mapboxgl.Marker({color: "#54108E"})
            .setLngLat(company.coords)
            .setPopup(popup)
            .addTo(map);
        });
      });

      // Add auto-refresh check
      $map.append("<div id='map-auto-refresh'><div id='map-auto-refresh-checkbox'><input type='checkbox'></input><span>Rechercher quand je déplace la carte<span></div></div>");
      $("#map-auto-refresh input").prop('checked', autoRefreshActivated);
      $("#map-auto-refresh input").change(function() {
          autoRefreshActivated = $(this).is(':checked');
      });

      var onMapMove = function() {
        if(autoRefreshActivated) {
          updateMap();
        }
        else {
            $("#map-auto-refresh").html("<a class='btn btn-small btn-info' href='#''>Relancer la recherche ici</a>").addClass();
            $("#map-auto-refresh a").click(function(e) {
                e.preventDefault();
                updateMap();
            });
        }
      };
      var onMapDrag = function() {
        onMapMove();
      };
      var onMapZoom = function(e) {
        if (e.initialZoom) {
          return;
        }
        onMapMove();
      };
      var onMapLoad = function() {
        $('.mapboxgl-ctrl-attrib .mapboxgl-ctrl-attrib-inner')
          .html('<a href="https://www.openstreetmap.org/copyright" target="_blank" title="© Contributeurs OpenStreetMap (ouverture dans un nouvel onglet)">&copy; Contributeurs OpenStreetMap</a>');
      }


      var updateMap = function() {
        center = map.getCenter();
        zoom = map.getZoom();

        $latitude.val(center.lat);
        $longitude.val(center.lng);

        // Adjust search radius
        var distances = [5, 10, 30, 50, 100, 3000];
        var earthPerimeterKm = 2 * 3.14159 * 6371;
        var earthPerimeterAtCompanyLocationKm = earthPerimeterKm * Math.cos(center.lat);
        // See leaflet.js zoom definition https://wiki.openstreetmap.org/wiki/Zoom_levels
        var pixelSizeKm = earthPerimeterAtCompanyLocationKm / (256 * Math.pow(2, zoom));
        var mapHeightPixels = map.getContainer().scrollHeight;
        var windowHeightKm = pixelSizeKm * mapHeightPixels * 2;// 2 is an arbitrary scaling factor to include results just ouside the bounding box
        var newDistance = distances[distances.length - 1];
        for(var d=0; d < distances.length; d++) {
            if(windowHeightKm < distances[d]) {
                newDistance = distances[d];
                break;
            }
        }
        $("input[name='d']").val(newDistance);

        // Clear the location field so that it gets auto-filled server-side
        var $location = $('#l');
        $location.attr('placeholder', $location.val());
        $location.val('');

        // remove department filter
        $("#departments").val('');

        $('.js-search-form').trigger('submit', {async: true});
      };
      map.on('dragend', onMapDrag);
      map.on('zoomend', onMapZoom);
      map.on('load', onMapLoad);
    } catch(e) {
      $map.hide();
      // hide again in the next event cycle, because somewhere we show the map
      setTimeout(function() { $map.hide(); });
    }
  }

  $(document).on('lbbready', function () {
      initResultsMap();
  });

})(jQuery);

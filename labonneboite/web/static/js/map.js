/* jshint esversion: 6 */
(function($) {
  let center = null;
  let zoom = null;

  function initResultsMap() {
    "use strict";
    let $mapContainer = $('#lbb-result-map');
    if (!$mapContainer.length) {
      return;
    }

    // TODO deduplicate this from results.js
    L.mapbox.accessToken = 'pk.eyJ1IjoibGFib25uZWJvaXRlIiwiYSI6ImNpaDNoN3A0cDAwcmdybGx5aXF1Z21lOGIifQ.znyUeU7KoIY9Ns_AQPquAg';

    let map = L.mapbox.map($mapContainer[0], 'mapbox.streets');
    let minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
    let companyCount = 0;

    // TODO: this is also duplicated code
    map.scrollWheelZoom.disable();

    $(".lbb-result__content__map").each(function() {
      let companyName = $(this).find('input[name="company-name"]').val();
      let lat = $(this).find('input[name="company-latitude"]').val();
      let lng = $(this).find('input[name="company-longitude"]').val();
      let siret = $(this).find('input[name="company-siret"]').val();

      let coords = [lat, lng];
      let link = "<a href='#company-" + siret + "'>" + companyName + "</a>";
      L.marker(coords).addTo(map).bindPopup(link).openPopup();

      companyCount += 1;
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
    });

    // Focus either on the companies or the requested coordinates
    if (center !== null && zoom !== null) {
      // Reset to the same position if we just moved the map
      map.setView(center, zoom);
    } else if (companyCount == 1) {
      map.setView([minLat, minLng], 13);
    } else if (companyCount > 0) {
      map.fitBounds([
        [minLat, minLng],
        [maxLat, maxLng]
      ]);
    } else {
      // TODO duplicate code from results.js
      var inputLatitude = $("#lat");
      var inputLongitude = $("#lon");
      map.setView([inputLatitude.val(), inputLongitude.val()], 13);
    }

    map.on('moveend', function() {
      center = this.getCenter();
      zoom = this.getZoom();

      // TODO this is pretty much duplicated from form.js
      $("#lat").val(center.lat);
      $("#lon").val(center.lng);

      // Adjust search radius
      let distances = [5, 10, 30, 50, 100, 3000];
      let distancePerPixel = 2 * 3.14159 * 6371 * Math.cos(center.lat) / (256 * Math.pow(2, zoom)); // TODO this requires an explanation
      let windowHeightKm = distancePerPixel * this.getSize().y * 2;// 2 is an arbitrary scaling factor to include results just ouside the bounding box
      let newDistance = distances[distances.length - 1];
      for(let d=0; d < distances.length; d++) {
          if(windowHeightKm < distances[d]) {
              newDistance = distances[d];
              break;
          }
      }
      $("input[name='d']").val(newDistance);

      $('.js-search-form').trigger('submit',
        // these options will be caught by the onsubmit function
        {
          async: true,
        }
      );
    });
  }

  $(document).on('lbbready', function () {
      initResultsMap();
  });

})(jQuery);

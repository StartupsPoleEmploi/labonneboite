"use strict";

/**
* Global function that tracks a click on an outbound link in Google Analytics.
* This function takes a valid URL string as an argument, and uses that URL string
* as the event label.
*/
var trackOutboundLink = function(url) {
  ga('send', 'event', 'outbound', 'click', url);
};

(function ($) {

  $(document).on('lbbready', function () {

    // Only init a map if its container is visible because Leaflet
    // has a hard time initializing maps in hidden elements.
    $('.js-map-container:visible').initMap();

    $('.js-result-toggle-details').toggleDetails();

    var eventLabel;
    if ($('.ga-no-results').length) {
      var eventLabel = "job:" + $('input[name="job"]').val() + ";location:" + $('input[name="location"]').val();
      ga('send', 'event', 'Resultats', 'no results', eventLabel);
    }

    $('.ga-pdf-download-link').click(function (e) {
      ga('send', 'event', 'Download', 'fiche entreprise', 1);
    });

  });

  /*
   * .initMap()
   *
   * Description:
   *   Init a Leaflet map.
   *
   * Usage:
   *   $('map-container-selector').initMap();
   *
   * Expected markup:
   *   - The container must contain a div with a `.map` class that is the map placeholder.
   *   - The container must contain some hidden inputs that will be used for building the map:
   *       * company-latitude
   *       * company-longitude
   *       * company-name
   *
   * Expected markup example:
   *   <div class="js-map-container">
   *     <input name="company-name" type="hidden" value="{{ company.name }}">
   *     <input name="company-longitude" type="hidden" value="{{ company.x }}">
   *     <input name="company-latitude" type="hidden" value="{{ company.y }}">
   *     <div class="map"></div>
   *   </div>
   */
  $.fn.initMap = function () {

    if (!this.length) {
      return;  // Stop here when no container is found.
    }

    this.each(function (index) {
      var $mapContainer = $(this);
      var companyName = $mapContainer.find('input[name="company-name"]').val();
      var lat = $mapContainer.find('input[name="company-latitude"]').val();
      var lng = $mapContainer.find('input[name="company-longitude"]').val();
      var coords = [lng, lat];
      var map = createMap($mapContainer.find('.map')[0], coords, 13);
      map.on("load", function() {
        var popup = new mapboxgl.Popup()
          .setHTML(companyName);
        var marker = new mapboxgl.Marker()
          .setLngLat(coords)
          .setPopup(popup)
          .addTo(map);

        // TODO ISOCHRONIE do we need this?
        // Add start marker
        //L.marker([locationLat, locationLon], {title: locationName}).addTo(map).bindPopup(locationName);
        //// Add company destination marker
        //L.marker(coords).addTo(map).bindPopup(companyName).openPopup();
        //// Add directions
        //$.getJSON("/maps/directions", {
          //from: locationLat + "," + locationLon,
          //to: lat + "," + lon,
          //tr: travelMode,
        //}, function(coordinates) {
          //// Note that we do not give any travel indications here, although it
          //// may be useful, for example for public transports
          //var polyline = L.polyline(coordinates, {color: '#7c408b'}).addTo(map);
          //// Fitting to the boundaries of the polyline is actually not very elegant
          ////map.fitBounds(polyline.getBounds());
        //}).fail(function() {
          //// die silently without warning the user
        //});
      });
      $mapContainer.find('.map').click(function (e) {
        e.stopPropagation();
      });
    });
  };


  /*
   * .toggleDetails()
   *
   * Description:
   *   Show or hide the details of a search result.
   */
  $.fn.toggleDetails = function () {

    var maps = [];

    $(this).click(function (e) {

      e.preventDefault();

      var $resultContainer = $(this).closest('.lbb-result');

      // If the clicked element is already active, hide it.
      if ($resultContainer.hasClass('active')) {
        $resultContainer.removeClass('active');
        return;
      }

      // Otherwise, show it.
      $resultContainer.addClass('active');

      // Track the click.
      var eventLabel = [
        'position:', $resultContainer.find('input[name="position"]').val(),
        ',effectif:', $resultContainer.find('input[name="headcount"]').val(),
        ',distance:', $resultContainer.find('input[name="company_distance"]').val(),
      ].join('');
      ga('send', 'event', 'Fiche Entreprise', 'Deplier', eventLabel);

      // Init the map.
      var siret = $resultContainer.find('input[name="company-siret"]').val();
      if ($.inArray(siret, maps) === -1) {
        $resultContainer.find('.js-map-container').initMap();  // Here, we know that the container is visible.
        maps.push(siret);
      }

      // Hide any already opened company block.
      $('.lbb-result')
        .not($resultContainer)
        .removeClass('active');

      // Trigger event
      $.post('/events/toggle-details/' + siret, {'csrf_token': CSRF_TOKEN});
    });

  };

})(jQuery);

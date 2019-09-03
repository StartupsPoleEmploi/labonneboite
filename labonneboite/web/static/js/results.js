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
    //updateTravelDurations();
    $('#shown-search-form').checkChanges();

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

  function updateTravelDurations() {
    // Compute travel durations asynchronously for each company
    var companySirets = [];
    var companyCoordinates = [];
    var latitude = $("#lat").val();
    var longitude = $("#lon").val();
    var travelMode = $("#tr").val() || "car";
    $(".travel-duration").each(function(){
        companySirets.push($(this).attr("data-siret"));
        companyCoordinates.push($(this).attr("data-latitude") + "," + $(this).attr("data-longitude"));
    });
    if (!companySirets.length) {
        return;
    }
    // Load durations 5 by 5 to avoid timeouts from upstream servers
    var sampleSize = 5;
    for (var i=0; i < companyCoordinates.length; i += sampleSize) {
      loadTravelDurations(
        travelMode, latitude, longitude,
        companyCoordinates.slice(i, i+sampleSize),
        companySirets.slice(i, i+sampleSize)
      );
    }
  }

  function loadTravelDurations(travelMode, latitude, longitude, companyCoordinates, companySirets) {
    $.ajax({
        url: "/maps/durations",
        method: 'POST',
        data: JSON.stringify({
          origin: latitude + "," + longitude,
          destinations: companyCoordinates,
          travel_mode: travelMode,
        }),
        contentType: 'application/json',
        dataType: 'json',
        headers: {
          "X-CSRFToken": CSRF_TOKEN,
        }
    }).success(function(durations) {
        // Fill durations
        for(var i = 0; i < durations.length; i += 1) {
            if(durations[i]) {
                // Convert duration from seconds to minutes
                var duration = durations[i] / 60;
                if(Math.floor(duration) < duration) {
                  duration += 1;
                }
                duration = Math.floor(duration);

                // Fill html
                var modes = {
                  'car': "en voiture",
                  'public': "en transports en commun",
                }
                var html = '<img class="img-icon-large" alt="Temps de transport nécessaire pour rejoindre cette société depuis le lieu de recherche" src="/static/images/icons/travel/' + travelMode + '-grey.svg"> ' + duration + ' min ' + modes[travelMode];
                $(".travel-duration[data-siret='" + companySirets[i] + "']").html(html);
            }
        }
    }).fail(function(e) {
      // In case of error, don't do anything
    });
  }


  $.fn.checkChanges = function () {
    var shown_form = this;
    var hidden_form = $('.js-search-form');
    var send_button = shown_form.find('button[type="submit"]');

    send_button.on('click', function (e) {
      e.preventDefault();
      e.stopPropagation();

      // Make sure new fields are displayed in the shown form.
      var location = shown_form.find('#l');
      var occupation = shown_form.find('#j');
      location.attr('value', location.prop('value'));
      occupation.attr('value', occupation.prop('value'));
      shown_form.submit();
    });

    shown_form.on('submit', function(e) {
      e.preventDefault();
      e.stopPropagation();
      var html_form = shown_form.html();
      hidden_form.find('#hidden-search-form').html(html_form);
      hidden_form.submit();
    });
  }

})(jQuery);
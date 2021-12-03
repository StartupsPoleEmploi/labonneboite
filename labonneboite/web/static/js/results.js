"use strict";

(function ($) {

  $(document).on('lbbready', function () {

    // Only init a map if its container is visible because Leaflet
    // has a hard time initializing maps in hidden elements.
    $('.js-map-container:visible').initMap();
    $('.js-result-toggle-details').toggleDetails();
    updateTravelDurations();
    $('#shown-search-form').checkChanges();
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

      // Get all URL params, used for activity logs
      var query = window.location.search.substring(1)
        .split('&')
        .reduce(function(acc, keyVal) {
          try {
            var [key, val] = keyVal.split('=');
            return {
              ...acc,
              [key]: val,
            }
          } catch(e) {
            // no destructuring support
            return acc
          }
        }, {})
      // Add CSRF token
      query['csrf_token'] = CSRF_TOKEN;
      // Trigger event
      $.post('/events/toggle-details/' + siret, query);
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
  }


  $.fn.checkChanges = function () {
    var shown_form = this;
    var hidden_form = $('.js-search-form');
    var send_button = shown_form.find('button[type="submit"]');

    // handle related rome initial search
    var related_rome_initial = $('#related_rome_initial');
    related_rome_initial.on('click', function(e) {
      var rome_description = $(e.target).attr('data-rome-description');
      var rome_description_slug = $(e.target).attr('data-rome-description-slug');
      if (rome_description && rome_description_slug) {
        var ij = hidden_form.find('#ij'); // initial search (related romes case)
        var j = shown_form.find('#j'); // j stands for job
        var hiddenJ = hidden_form.find('#j'); // this is the same "job" param, in the hidden form
        var occupation = hidden_form.find('#occupation');
        ij.val('');
        j.val(rome_description);
        hiddenJ.val(rome_description);
        occupation.val(rome_description_slug);
        hidden_form.submit();
      } else {
        // we clicked outside the <a /> tag
        e.preventDefault();
      }
    })

    // trigger hotjar
    if (related_rome_initial.length > 0 && window.hj) {
      window.hj('trigger', 'related_rome_search');
    }

    // handle related romes
    var related_romes = $('#form-related_romes');
    related_romes.on('click', function(e) {
      var rome_description = $(e.target).attr('data-rome-description');
      var rome_description_slug = $(e.target).attr('data-rome-description-slug');
      if (rome_description && rome_description_slug) {
        var ij = hidden_form.find('#ij'); // initial search (related romes case)
        var j = shown_form.find('#j'); // j stands for job
        var hiddenJ = hidden_form.find('#j'); // this is the same "job" param, in the hidden form
        var occupation = hidden_form.find('#occupation');
        ij.val(j.val());
        j.val(rome_description);
        hiddenJ.val(rome_description);
        occupation.val(rome_description_slug);
        hidden_form.submit();
      } else {
        // we clicked outside the <a /> tag
        e.preventDefault();
      }
    });

    // trigger hotjar
    if (related_romes.length > 0 && window.hj) {
      window.hj('trigger', 'related_rome_suggest');
    }

    send_button.on('click', function (e) {
      e.preventDefault();
      e.stopPropagation();

      // Make sure new fields are displayed in the shown form.
      var location = shown_form.find('#l');
      var occupation = shown_form.find('#j');
      location.attr('value', location.prop('value'));
      occupation.attr('value', occupation.prop('value'));

      // Remove related rome initial search.
      var ij = hidden_form.find('#ij');
      ij.val('');

      // Submit the form.
      shown_form.submit();
    });

    shown_form.on('submit', function(e) {
      // Reset the "naf" filter (Secteur d'activité)
      // This is a quick fix to this problem: if the user changes the search location or job when she has previously selected a naf, the new search might not have result with the selected naf, so the selected naf will not appear in the dropdown which will display "tous les secteurs" while still filtering the results with the naf
      // @see https://trello.com/c/Y6iboXeE/603-ano-erreur-valorisation-filtre-secteur-dactivit%C3%A9
      $('#naf').val('')

      e.preventDefault();
      e.stopPropagation();
      var html_form = shown_form.html();
      hidden_form.find('#hidden-search-form').html(html_form);
      hidden_form.submit();
    });
  }

})(jQuery);

"use strict";

(function ($) {

  // Based on:
  // https://github.com/scottgonzalez/jquery-ui-extensions/blob/master/src/autocomplete/jquery.ui.autocomplete.html.js
  // Removed initSource and filter function to enable html autocomplete on ajax source.
  // ---------------------------------------------

  var proto = $.ui.autocomplete.prototype;
  var initSource = proto._initSource;

  $.extend(proto, {
    _initSource: function () {
      initSource.call(this);
    },
    _renderItem: function (ul, item) {
      var stuff = $("<li></li>")
        .data("item.autocomplete", item)
        .append($("<a></a>")[this.options.html ? "html" : "text"](item.label))
        .appendTo(ul);
      return stuff;
    }
  });

  // Search form with autocompletes.
  // ---------------------------------------------

  // Form.
  var searchForm = $('.js-search-form');

  // Inputs.
  var inputJob = $("input[name='job']");
  var inputOccupation = $('#occupation');
  var inputLocation = $("input[name='location']");
  var inputZipcode = $("#zipcode");
  var inputCity = $("#city");

  var initialOccupation = inputOccupation.val()

  // Job.
  var setJob = function (item) {
    if (item) {
      inputOccupation.val(item.occupation);
    }
  }
  var resetJob = function () {
    inputJob.val('');
    inputOccupation.val('');
  };

  // Location.
  var setLocation = function (item) {
    if (item) {
      inputZipcode.val(item.zipcode);
      inputCity.val(item.city);
    }
  }
  var resetLocation = function () {
    inputLocation.val('');
    inputZipcode.val('');
    inputCity.val('');
  };

  var getLocationsFromLBB = function (request, responseCB) {
    $.getJSON('/suggest_locations?term=' + request.term, function (lbb_response) {
      responseCB(lbb_response);
    });
  }

  $(document).ready(function () {

      if (!inputJob.val()) {
        inputJob.focus();
      }

      // Configure autocompletes.
      inputJob.autocomplete({
        delay: 200,
        html: true,
        minLength: 2,
        position: {my: "left top", at: "left bottom"},
        open: function (event, ui) {
          $('.ui-autocomplete').off('menufocus hover mouseover mouseenter');
        },
        source: "/suggest_job_labels",
        response: function (event, ui) {
          if (ui.content) {
            // Auto-set the first result just in case the user does not click on an autocomplete suggestion.
            setJob(ui.content[0]);
          }
        },
        select: function (event, ui) {
          setJob(ui.item);
          // The TAB key will set the focus on the next element. If another key is pressed, set the focus.
          if (event.keyCode !== 9) {
            inputLocation.val().length ? searchForm.find(':submit').focus() : inputLocation.focus();
          }
        },
      });
      inputLocation.autocomplete({
        delay: 200,
        html: true,
        minLength: 2,
        position: {my: "left top", at: "left bottom"},
        open: function (event, ui) {
          $('.ui-autocomplete').off('menufocus hover mouseover mouseenter');
        },
        source: getLocationsFromLBB,
        response: function (event, ui) {
          if (ui.content) {
            // Auto-set the first result just in case the user does not click on an autocomplete suggestion.
            setLocation(ui.content[0]);
          }
        },
        select: function (event, ui) {
          setLocation(ui.item);
          // The TAB key will set the focus on the next element. If another key is pressed, set the focus.
          if (event.keyCode !== 9) {
            inputJob.val().length ? searchForm.find(':submit').focus() : inputJob.focus();
          }
        },
      });

      // Reset any previous result.
      inputJob.on('mousedown', resetJob);
      inputLocation.on('mousedown', resetLocation);

      // When the search form is submitted.
      searchForm.on('submit', function () {
        // Reset the "naf" (business sector) filter when a new search is performed.
        if (initialOccupation && initialOccupation !== inputOccupation.val()) {
          $("#naf").val('')
        }
        // Disable the submit button and display a spinner.
        searchForm.find('button:submit').prop('disabled', true);
        searchForm.find('button:submit img').remove();
        searchForm.find('.spinner').removeClass('hidden');
      });

      // Auto-submit the search form when any form element is changed in the sidebar.
      $('.js-form-search-filters :input').on('change', function () {
        searchForm.submit();
      });

      // Auto-submit the search form when a link to expand the search results by occupation is clicked.
      $('.js-extend-search-occupation').click(function (e) {
        e.preventDefault();
        inputOccupation.val(this.dataset.occupation);
        searchForm.submit();
      });

      // Auto-submit the search form when a link to expand the search results by distance is clicked.
      $('.js-extend-search-distance').click(function (e) {
        e.preventDefault();
        $(':radio[name=distance][value=' + this.dataset.distance + ']').prop('checked', true);
        searchForm.submit();
      });

  });

})(jQuery);

(function($) {

  $(document).on('lbbready', function () {
    $().updateTextAndMap();
    $('#map-switch-button, #map-switch-text').switchButton();
  });


  $.fn.switchButton = function () {
    var switchButton = $(this);
    switchButton.on('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      $().updateMapInput();
      $().updateTextAndMap();
    });
  };

  $.fn.updateMapInput = function () {
      var inputCheckbox = $('#toggle-map');
      if (inputCheckbox.is(':checked')) {
          inputCheckbox.prop('checked', false);
      } else {
          inputCheckbox.prop('checked', true);
      }
  };


  $.fn.updateTextAndMap = function () {
      var inputCheckbox = $('#toggle-map');
      var textContainer = $('#map-switch-text');
      var map = $('#lbb-result-map');

      if (inputCheckbox.is(':checked')) {
          textContainer.text('Masquer la carte');
          map.slideDown();
      } else {
          textContainer.text('Afficher la carte')
          map.slideUp();
      }

      return this;
  };

})(jQuery);

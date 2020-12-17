"use strict";

(function($) {
  $(document).on('lbbready', function () {
    $('[data-toggle="tooltip"]').tooltip();  // Activate tooltips site wide.
    $('[data-toggle="tooltip"][data-show]').tooltip('show');  // Activate tooltips site wide.
  });
})(jQuery);

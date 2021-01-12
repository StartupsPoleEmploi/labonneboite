"use strict";

(function($) {
  $(document).on('lbbready', function () {
    // Activate tooltips site wide
    $('[data-toggle="tooltip"]').tooltip();
    // Handle auto tooltips
    $('[data-toggle="tooltip"][data-show]')
      .tooltip('show')
      .each(function() {
        // Hide it on hover out
        var $this = $(this);
        var id = $this.attr('aria-describedby');
        $('#' + id).mouseleave(function() {
          $this.tooltip('hide');
        });
      });
  });
})(jQuery);

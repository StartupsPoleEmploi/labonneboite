(function($) {

  $(document).ready(function () {

    // Handle cases where there is a click outside of a dropdown.
    $(document).on('click', function (e) {
      if ($(e.target).closest('.lbb-dropdown-wrapper').length) {
        // Do not close the dropdown when a click is inside it.
        return;
      }
      $.deactivateAllDropdowns();
    });

    $('.lbb-dropdown-wrapper > a').toggleDropdown();

  });

  $.fn.toggleDropdown = function () {

    $(this).on('click', function (e) {

      e.preventDefault();
      e.stopPropagation();  // Do not propagate up to the $(document) click event which closes all dropdowns.

      var $wrapper = $(this).closest('.lbb-dropdown-wrapper');
      var $dropdown = $wrapper.find('.lbb-dropdown');

      if ($wrapper.hasClass('active')) {
        $.deactivateAllDropdowns();  // Including this one.
        return;
      }

      // Deactivate all dropdowns just for the case where another dropdown is already active.
      $.deactivateAllDropdowns();
      // Activate the current dropdown.
      $wrapper.addClass('active');
      $dropdown.css('display', 'block');

    });

  };

  jQuery.deactivateAllDropdowns = function () {
    $('.lbb-dropdown-wrapper').removeClass('active');
    $('.lbb-dropdown').css('display', 'none');
  };

})(jQuery);

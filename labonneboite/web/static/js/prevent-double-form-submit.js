(function($) {

  $(document).ready(function () {

    // Prevent form double submit system wide.
    $('form').on('submit', function () {
      $(':submit', this).on('click', function () {
        return false;
      });
    });

  });

})(jQuery);

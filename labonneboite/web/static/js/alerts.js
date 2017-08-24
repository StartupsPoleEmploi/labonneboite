(function($) {

  $(document).ready(function () {
    $('.js-alert-close').addCloseButton();
  });

  $.fn.addCloseButton = function () {
    $(this).prepend('<a href="#" class="alert__close">&times;</a>');
    var $close = $(this).find('.alert__close')
    $close.on('click', function (e) {
      e.preventDefault();
      $(this).closest('.alert').slideUp(200, function () {
        $(this).remove();
      });
    });
  };

})(jQuery);

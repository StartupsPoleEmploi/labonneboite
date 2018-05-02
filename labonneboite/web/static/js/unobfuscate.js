"use strict";

(function ($) {

  $(document).on('lbbready', function () {
    $('.js-obfuscated-email').unobfuscate();
  });

  $.fn.unobfuscate = function () {
    var elements = this;
    if (elements.length) {
      elements.each(function () {
        var reversed = $(this).text().split('').reverse().join('');
        $(this)
          .removeClass('js-obfuscated-email')
          .html('<a href="mailto:'+ reversed +'">Contact</a>');
      });
    }
    return this;
  };

})(jQuery);

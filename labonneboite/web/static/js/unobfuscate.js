"use strict";

(function ($) {

  $(document).on('lbbready', function () {
    $('.js-obfuscated-email').unobfuscate();
  });

  $.fn.unobfuscate = function () {
    var elements = this;
    if (elements.length) {
      elements.each(function () {
        var $this = $(this);

        var reversed = $this.text().split('').reverse().join('');

        var title = $this.attr('data-title') || 'Nous contacter par e-mail';

        var mailSubject = $this.attr('data-subject');
        if(mailSubject) reversed = reversed + '?subject=' + encodeURIComponent(mailSubject);

        $(this)
          .removeClass('js-obfuscated-email')
          .html('<a title="' + title + '" href="mailto:'+ reversed +'">Contact</a>');
      });
    }
    return this;
  };

})(jQuery);

"use strict";

(function($) {

  $(document).ready(function () {

    var cookieName = 'cookie-stop';
    var bannerElement = $('.cookies-banner');

    if (Cookies.get(cookieName) === undefined) {
      bannerElement.show()
      $('.cookies-accept').on('click', function (e) {
        e.preventDefault();
        Cookies.set(cookieName, true, { expires: 12 });
        bannerElement.hide()
      })
    }

  });

})(jQuery);

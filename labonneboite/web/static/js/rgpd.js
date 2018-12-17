"use strict";

var cookieName = 'rgpd-consent';

// RGPD consent has 3 possible states:
// accepted (opt in), rejected (opt out), and undecided yet (default)

function userHasOptOutRGPD() {
  return (Cookies.get(cookieName) === "false")
}

function userHasOptInRGPD() {
    return (Cookies.get(cookieName) === "true")
}

function userHasNotYetDecidedRGPD() {
    return (Cookies.get(cookieName) === undefined)
}

(function($) {

    $(document).on('lbbready', function () {

    var bannerElement = $('.rgpd-banner');

    if (userHasNotYetDecidedRGPD()) {
      bannerElement.show();
      ga('send', 'event', 'RGPD', 'banner');
    }

    $('.rgpd-accept').on('click', function (e) {
      e.preventDefault();
      Cookies.set(cookieName, true, { expires: 365 });
      bannerElement.hide();
      closeModals();
      ga('send', 'event', 'RGPD', 'accept');
    });

    $('.rgpd-reject').on('click', function (e) {
      e.preventDefault();
      Cookies.set(cookieName, false, { expires: 365 });
      bannerElement.hide();
      closeModals();
      ga('send', 'event', 'RGPD', 'reject');
    });

    $('.rgpd-info').on('click', function (e) {
      e.preventDefault();
      showModal("#rgpd-modal");
      ga('send', 'event', 'RGPD', 'info');
    });

    $('.rgpd-consent-required').on('click', function (e) {
      if (userHasOptInRGPD() === false) {
        alert('Vous devez accepter notre politique de confidentialité pour utiliser notre service.');
        closeModals();
        $(".lbb-dropdown").hide();  // hide PE connect dropdown
        showModal("#rgpd-modal");
        e.preventDefault();
        ga('send', 'event', 'RGPD', 'required');
      }
    });

    $('.rgpd-account-download-personal').on('click', function (e) {
      ga('send', 'event', 'RGPD', 'account-download-personal');
    });

    $('.rgpd-account-download-favorites').on('click', function (e) {
      ga('send', 'event', 'RGPD', 'account-download-favorites');
    });

    $('.rgpd-account-delete-attempt').on('click', function (e) {
      ga('send', 'event', 'RGPD', 'account-delete-attempt');
    });

    $('.rgpd-account-delete-confirm').on('click', function (e) {
      ga('send', 'event', 'RGPD', 'account-delete-confirm');
    });

  });

})(jQuery);

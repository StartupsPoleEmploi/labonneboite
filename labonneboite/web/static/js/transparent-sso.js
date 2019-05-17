(function($) {
    var sso_storage_entry = 'sso-last-attempt';

    function bindMessageEventToWindow() {
        // Receive message from child iframe
        var eventHandler = function (e) {
            if (e.data === 'USER_SSO_CONNECTED') {
                // Refresh user header
                $.get('/user/header.html', function(data) {
                    $('#user-header').html(data);
                });
            }
        };
        if (window.addEventListener) {
            // Standard support for event propagation
            window.addEventListener('message', eventHandler, false);
        } else if (window.attachEvent) {
            // Microsoft IE8 support
            window.attachEvent('onmessage', eventHandler);
        }
    }

    // In case of error, the authentication backend might redirect to the
    // origin location. That means that the landing page (or any other) will
    // be loaded inside the invisible iframe. In such cases we don't want to
    // trigger transparent SSO, otherwise we will end up with infinitely
    // included iframes.
    if (window.parent === window) {
      // "idutkes" is the name of the cookie dropped by PE.fr
      var connectedOnPE = Cookies.get("idutkes")? true : false;

      // We don't want to flood the authentication backend, so if a
      // connection attempt fails, we do not retry for two hours.
      var now = new Date().getTime();
      var lastAttempt = localStorage.getItem(sso_storage_entry);
      var canAttemptSSO = lastAttempt === null || now - parseFloat(lastAttempt) > 2*60*60*1000;

      if (!window.USER_IS_AUTHENTICATED && connectedOnPE && canAttemptSSO) {
          bindMessageEventToWindow();

          // Make a call to the authentication backend inside an iframe. The
          // redirect is an url that will signal the parent window (this one)
          // with a USER_SSO_CONNECTED message if the user is correctly connected.
          var iframeUrl = window.location.protocol + '//' + window.location.host + '/authentication/iframe';
          var peamURL = window.location.origin + '/authorize/login/peam-openidconnect-no-prompt/?keep=1&next=' + encodeURIComponent(iframeUrl);
          var ifr = document.createElement("iframe");
          ifr.setAttribute("src", peamURL);
          ifr.setAttribute('aria-hidden', 'true');
          ifr.setAttribute('title', 'Dispositif technique (aucun contenu)');
          ifr.setAttribute("style", "display:none;");
          document.body.appendChild(ifr);
          localStorage.setItem(sso_storage_entry, now);
      }
    }
}(jQuery));

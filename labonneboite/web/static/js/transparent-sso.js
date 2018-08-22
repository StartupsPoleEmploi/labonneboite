(function($) {
    var sso_storage_entry = 'sso-last-attempt';

    function bindMessageEventToWindow() {
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

    // We don't want to flood the authentication backend, so if a
    // connection attempt fails, we do not retry for two hours.
    var now = new Date().getTime();
    var lastAttempt = localStorage.getItem(sso_storage_entry);
    var canAttemptSSO = lastAttempt === null || now - parseFloat(lastAttempt) > 2*60*60*1000;

    if (!window.USER_IS_AUTHENTICATED && Cookies.get("idutkes") && canAttemptSSO) {
        // User is authenticated on PE.fr but not on LBB
        bindMessageEventToWindow();

        // Make a call to the authentication backend inside an iframe. The
        // redirect is an url that will signal the parent window (this one)
        // with a USER_SSO_CONNECTED message if the user is correctly connected.
        var iframeUrl = window.location.protocol + '//' + window.location.host + '/authentication/iframe';
        var peamURL = window.location.origin + '/authorize/login/peam-openidconnect-no-prompt/?next=' + encodeURIComponent(iframeUrl);
        var ifr = document.createElement("iframe");
        ifr.setAttribute("src", peamURL);
        ifr.setAttribute("style", "display:none;");
        document.body.appendChild(ifr);
        localStorage.setItem(sso_storage_entry, now);
    }
}(jQuery));

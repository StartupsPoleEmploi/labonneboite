/* jshint esversion: 6 */

window.$openingButton = undefined;
window.$focusables = undefined;
window.focusableIndex = 0;


var FOCUSABLE_ELEMENTS = 'a[href], area[href], input:not([disabled]):not([type="hidden"]):not([aria-hidden]), select:not([disabled]):not([aria-hidden]), textarea:not([disabled]):not([aria-hidden]), button:not([disabled]):not([aria-hidden]), iframe, object, embed, [contenteditable], [tabindex]:not([tabindex^="-"])';

function closeModals() {
    if (jQuery(".modal").not(".modal-closed")) {
        ga('send', 'event', 'Modal', 'close');
        jQuery(".modal").addClass("modal-closed");
        jQuery(".modal").attr("aria-hidden", "true");
        jQuery(".modal-overlay").addClass("modal-closed");
    }

    // When closing the modal, we need to return to the opening button
    if(window.$openingButton) {
        window.$openingButton.focus()
        window.$openingButton = undefined;
    }

    // Clear focusable elements data
    window.$focusables = undefined;
    window.focusableIndex = 0;

    // Make the scroll back
    jQuery('html').removeClass('lock-scroll');
}

function focusToNext() {
    window.focusableIndex = window.focusableIndex + 1;
    if (window.focusableIndex >= window.$focusables.length) window.focusableIndex = 0;
    window.$focusables.get(window.focusableIndex).focus();
}
function focusToPrevious() {
    window.focusableIndex = window.focusableIndex - 1;
    if (window.focusableIndex < 0) window.focusableIndex = window.$focusables.length - 1;
    window.$focusables.get(window.focusableIndex).focus();
}

function showModal(selector) {
    var $modal = jQuery(selector);
    $modal.removeClass("modal-closed");
    $modal.attr("aria-hidden", "false");

    jQuery(".modal-overlay").removeClass("modal-closed");

    // Save opening button for later
    window.$openingButton = jQuery(document.activeElement);

    // Remove scroll
    jQuery('html').addClass('lock-scroll');

    // Save all focusable elements in modal + init counter + First focus
    window.$focusables = $modal.find(FOCUSABLE_ELEMENTS);
    window.focusableIndex = 0;
    window.$focusables.get(window.focusableIndex).focus();

    // Click on close button
    jQuery(".modal-close-button").one("click", function() {
        closeModals();
    });

    // Click outside of modal
    jQuery(".modal-overlay").one("click", function() {
        closeModals();
    });
}

// Capture escape key
jQuery("body").keydown(function(evt) {
    var TAB_KEY = 9;
    var ECHAP_KEY = 27;

    if (evt.which == ECHAP_KEY) closeModals();

    if (jQuery(".modal").not(".modal-closed").length) {
        // Shift+Tab : focus to previous element
        if (evt.shiftKey && evt.keyCode == TAB_KEY) {
            evt.preventDefault();
            focusToPrevious();
        // Tab : focus to next element
        } else if (evt.keyCode == TAB_KEY) {
            evt.preventDefault();
            focusToNext();
        }
    }
});

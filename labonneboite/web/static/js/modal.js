/* jshint esversion: 6 */

function closeModals() {
    if (jQuery(".modal").not(".modal-closed")) {
        ga('send', 'event', 'Modal', 'close');
        jQuery(".modal").addClass("modal-closed");
        jQuery(".modal-overlay").addClass("modal-closed");
    }
}

function showModal(selector) {
    jQuery(selector).removeClass("modal-closed");
    jQuery(".modal-overlay").removeClass("modal-closed");

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
    if (evt.which == 27) {
        closeModals();
    }
});

"use strict";

(function($) {

  $(document).ready(() => {

    $(document).on("click", "#pro-mode", (event) => {
        let $a = $(event.target);
        var action = $a.attr("data-action"); // Enable or disable ?

        if(action) {
            $.get("user/pro-mode?action=" + action)
            // Reload on success
            .done(() => window.location.reload())
            // Display error on fail
            .fail(() => {
                let message = (action == "enabled" ? "Erreur lors de l'activation du mode PRO": "Erreur lors de la désactivation du mode PRO");
                alert(message); 
            })
        }
    });
  });

})(jQuery);

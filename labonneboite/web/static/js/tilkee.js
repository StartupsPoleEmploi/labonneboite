/* jshint esversion: 6 */
(function($) {
    "use strict";

    var $tilkeeModal = $("#tilkee-modal .modal-content");
    function updateModal(html) {
        $tilkeeModal.html(html);
    }

    function showIntro() {
        var lastDisplay = localStorage.getItem("lastTilkeeIntroDisplay");
        var now = new Date().getTime();
        // Display Tilkee intro once per user and per month
        if (!lastDisplay || now-parseFloat(lastDisplay) > 30*24*60*60*1000) {
            localStorage.setItem("lastTilkeeIntroDisplay", now);
            showModal("#tilkee-modal");
        }
    }

    function initTilkeeModal(siret) {
        // Display modal with spinner
        showModal("#tilkee-modal");
        updateModal('<div class="modal-content-inner text-center"><span class="spinner spinner-dark"></span></div>');
        ga('send', 'event', 'Tilkee', 'show', siret);
    }

    function initUploadForm(siret) {
        // Handle file selection
        var files = [];
        $tilkeeModal.find('.tilkee-file-select').on("click", function(e){
            e.preventDefault();
            $tilkeeModal.find("[name='files']").click();
            ga('send', 'event', 'Tilkee', 'browse-files', siret);
        });
        $tilkeeModal.find("[name='files']").on("change", function(e){
            var newfiles = $(this).prop("files");
            // FIXME duplicate code from tilkee/utils.py
            var allowedExtensions = ['.doc', '.docx', '.jpeg', '.jpg', '.mov', '.mp4', '.pdf', '.png'];
            for (var f = 0; f < newfiles.length; f++) {
                var filename = newfiles[f].name;
                var fileExt = '.' + filename.split('.').pop().toLowerCase();
                if (allowedExtensions.indexOf(fileExt) < 0) {
                    // Yes, this is a js alert which is ugly
                    alert("Format de document non autorisé pour le fichier " + filename);
                } else {
                    files.push(newfiles[f]);
                }
            }
            drawFileList(files, siret);
        });

        $tilkeeModal.find(".tilkee-upload-form").on("submit", function(evt) {
            evt.preventDefault();
            uploadDocuments($(this), siret, files);
        });
    }

    function initUploadedButtons() {
        $tilkeeModal.find(".tilkee-copy-text button").click(function() {
            copyToClipboard('tilkee-email-body');
            $(this).html("<img class='tilkee-copy-tick' src='/static/images/icons/tick.svg'>");
        });
    }

    function drawFileList(files, siret) {
        var $fileList = $tilkeeModal.find(".tilkee-files");
        $fileList.html("");
        for (var f = 0; f < files.length; f++) {
            var filename = files[f].name;
            $fileList.append("<span><b>" + filename + "</b> <img class='tilkee-remove-file' alt='Retirer le fichier' src='/static/images/icons/times.svg' data-file-index='" + f + "'><span><br />\n");
        }
        if (files.length) {
            $tilkeeModal.find("[type='submit']").removeClass("hidden");
            ga('send', 'event', 'Tilkee', 'select-files', siret);
        } else {
            $tilkeeModal.find("[type='submit']").addClass("hidden");
            ga('send', 'event', 'Tilkee', 'select-no-file', siret);
        }
        $fileList.find(".tilkee-remove-file").click(function(){
            ga('send', 'event', 'Tilkee', 'remove-file');
            var f = $(this).attr("data-file-index");
            files.splice(parseInt(f), 1);
            drawFileList(files, siret);
        });
    }

    function uploadDocuments($form, siret, files) {
        var formData = new FormData();
        formData.set("csrf_token", $form.find("[name='csrf_token']")[0].value);
        for (var f = 0; f < files.length; f++) {
            formData.append('files', files[f], files[f].name);
        }

        $form.find("[type='submit']").prop("disabled", true);
        $.ajax({
            url: $form.attr("action"),
            type: 'POST',
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            success: function(html) {
                updateModal(html);
                initUploadedButtons();
                ga('send', 'event', 'Tilkee', 'upload', siret);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                if (jqXHR.status === 413) {
                    updateModal("Vos documents sont de trop grande taille : veuillez sélectionner des documents dont la taille totale est inférieure à 10 Mo.");
                } else if (jqXHR.status >= 500) {
                    updateModal("Une erreur inattendue s'est produite : nos équipes ont été prévenues et vont essayer de résoudre le problème très rapidement. Merci de réessayer plus tard.");
                } else {
                    updateModal("Erreur " + String(jqXHR.status) + " : est-ce que par hasard vous n'auriez pas essayé de faire quelque chose de fourbe ?");
                }
                ga('send', 'event', 'Tilkee', 'upload-error', siret);
            },
            complete: function() {
                $form.find("[type='submit']").prop("disabled", false);
            },
            xhr: function() {
                // Monitor upload progress
                var $messageElt = $tilkeeModal.find(".upload-progress-message");

                $tilkeeModal.find(".progressbar").removeClass("hidden");
                $messageElt.removeClass("hidden");
                var xhr = $.ajaxSettings.xhr();
                if (xhr.upload) {
                    xhr.upload.addEventListener('progress', function(e) {
                        if (e.lengthComputable) {
                            var percentage = e.loaded * 100/e.total;
                            $tilkeeModal.find(".progressbar span").css("width", String(percentage) + "%");
                            if (percentage < 100) {
                                $messageElt.html("1/2 Envoi de vos fichiers...");
                            } else {
                                $messageElt.html("2/2 Création de votre dossier...");
                            }
                        }
                    } , false);
                }
                return xhr;
            },
        });
    }

    $(document).on('lbbready', function() {
        showIntro();

        $(".tilkee-button").on("click", function(e) {
            e.preventDefault();
            $(this).tooltip("hide");
            var siret = $(this).attr("data-siret");
            initTilkeeModal(siret);

            // Load modal content
            $.get($(this).attr("href"), function(data) {
                updateModal(data);
                initUploadForm(siret);
            }).fail(function(e) {
                updateModal("Une erreur a eu lieu. Veuillez réessayer plus tard.");
            });

        });
    });
})(jQuery);

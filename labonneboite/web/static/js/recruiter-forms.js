(function ($) {

  var FORM_STORAGE_KEY = "FORM_IDENTIFICATION_VALUES";

  function initJobFormHandler() {
    "use strict";

    // Handle when user click on the 'Supprimer' button
    $(document).on('click', '.update-jobs-form table.jobs button.remove', function(event) {
      event.preventDefault();
      var $input = $(event.target);
      var $tr = $input.parents('tr');

      var doRemove = !$tr.hasClass('removed');

      if(doRemove) disableRow($tr);
      else enableRow($tr, true);
    });

    // Trigger 'click' on 'Supprimer' when user disabled all checkboxes
    $(document).on('click', '.update-jobs-form table.jobs input:not(.hide)', function(event) {
      var $input = $(event.target);

      var $tr = $input.parents('tr');
      var $nestedInputs = $tr.find('input:not(.hide)');

      var lbbCheckbox = $($nestedInputs.get(0));
      var lbaCheckbox = $($nestedInputs.get(1));

      // User change is mind and want to un-delete the job
      if((lbbCheckbox.prop('checked') || lbaCheckbox.prop('checked')) && $tr.hasClass('removed')) { enableRow($tr); }
      // User unchecked all checkbox
      else if(!lbbCheckbox.prop('checked') && !lbaCheckbox.prop('checked')) { disableRow($tr, false); }
    });
  }

  function disableRow($tr) {
    var $nestedInputs = $tr.find('input:not(.hide)');
    var $hideInput = $tr.find('input.hide');
    var $input = $tr.find('button.remove');

    $tr.addClass('removed');
    $nestedInputs.each(function(index, el) { $(el).prop('checked', false); });
    $hideInput.prop('checked', true);
    $input.text('Rajouter');
  }

  function enableRow($tr, checkAll) {
    var $nestedInputs = $tr.find('input:not(.hide)');
    var $hideInput = $tr.find('input.hide');
    var $input = $tr.find('button.remove');

    $tr.removeClass('removed');
    if(checkAll) $nestedInputs.each(function(index, el) { $(el).prop('checked', true); });
    $hideInput.prop('checked', false);
    $input.text('Supprimer');
  }


  // Save user data when submitting the identification form
  $('.identification-form').submit(function(e) {
    $form = $(e.target);

    var siret     = $form.find("input[name='siret']").val() || '';
    var lastName  = $form.find("input[name='last_name']").val() || '';
    var firstName = $form.find("input[name='first_name']").val() || '';
    var phone     = $form.find("input[name='phone']").val() || '';
    var email     = $form.find("input[name='email']").val() || '';

    localStorage.setItem(FORM_STORAGE_KEY, JSON.stringify({ siret, lastName, firstName, phone, email }));
  });

  function addLastSubmittedValue() {
    if($('.identification-form').length > 0) {
      var $form = $('.identification-form');

      var rawValues = localStorage.getItem(FORM_STORAGE_KEY);
      if(!rawValues) return;

      var values = {};
      try {
        values = JSON.parse(rawValues);
      } catch(error) {
        console.log(error);
        return;
      }

      // Do not override value if the siret (coming from URL parameter) is already here
      var $siret = $form.find("input[name='siret']");
      if(!$siret.val()) $siret.val(values.siret);

      // Do not override last_name/first_name/email is data comes from PE Connect
      var isConnectedRecruiter = $('[data-esd-recruiter="true"]').length > 0;

      if(!isConnectedRecruiter) {
        $form.find("input[name='last_name']").val(values.lastName);
        $form.find("input[name='first_name']").val(values.firstName);
        $form.find("input[name='email']").val(values.email);
      }
      $form.find("input[name='phone']").val(values.phone);

    }
  }

  function disablePeamRecruiterFields() {
    if($('.identification-form').length > 0) {
      var $form = $('.identification-form');
      var isConnectedRecruiter = $('[data-esd-recruiter="true"]').length > 0;
      if(!isConnectedRecruiter) return;

      $form.find("input[name='last_name']").attr('disabled', 'disabled');
      $form.find("input[name='first_name']").attr('disabled', 'disabled');
      $form.find("input[name='email']").attr('disabled', 'disabled');
    }
  }

  // JOB AUTO-COMPLETE
  var $newJobTable = $('.add-new-jobs table');
  var $newJobTbody = $newJobTable.find('tbody');
  var $newJobInput = $('.add-new-jobs input[name=new-job]');
  var jobRowTemplate = '<tr id="{ROME}"><td class="text-left"><b>{LABEL}</b></td>' +
      '<td class="text-center"><label for="lbb-{ROME}" class="sr-only">Intéressé par les candidatures pour le métier de {LABEL}</label><input checked="checked" id="lbb-{ROME}" type="checkbox" name="{ROME}" value="lbb" /></td>' +
      '<td class="text-center"><label for="lbb-{ROME}" class="sr-only">Ouvert aux contrats d\'alternance pour le métier de {LABEL}</span><input checked="checked" id="lbb-{ROME}" type="checkbox" name="{ROME}" value="lba" /></td>' +
      '<td class="text-center"><button class="btn remove" data-rome="{ROME}" title="Supprimer le métier {LABEL}">Supprimer<span class="sr-only">le métier de {LABEL}</span></button></td></tr>';

  $newJobInput.autocomplete({
    delay: 200,
    html: true,
    minLength: 2,
    position: {my: "left top", at: "left bottom"},
    open: function (event, ui) {
      $('.ui-autocomplete').off('menufocus hover mouseover mouseenter');
    },
    source: "/suggest_job_labels",
    select: function (event, ui) {
      addJob(ui.item.id, ui.item.label)
    },
    close: function(event, ui) {
      $newJobInput.val('');
    }
  });

  function addJob(rome, label) {
    // Handle if job already exists
    var alreadyExists = $('form tr#' + rome).length !== 0;
    if(alreadyExists) {
      alert('Le métier "' + label + '" est déjà présent.');
      return;
    }

    var rowHTML = renderTemplate(jobRowTemplate, { ROME: rome, LABEL: label })
    $newJobTbody.append($(rowHTML));
    $newJobTable.removeClass("hidden");
  }


  // Avoid submitting form when pressing 'enter'
  $newJobInput.keydown(function(event) {
    if (event.keyCode == 13) event.preventDefault();
  });

  // Remove added job
  $(document).on('click', '.add-new-jobs table button.remove', function(event) {
    event.preventDefault();
    var rome = $(event.target).attr('data-rome');
    $('form tr#' + rome).remove();

    if($newJobTbody.find('tr').length === 0) $newJobTable.addClass("hidden");
  });

  // http://mir.aculo.us/2011/03/09/little-helpers-a-tweet-sized-javascript-templating-engine/
  function renderTemplate(template_str, values){
    for(var value in values) {
      var pattern = '{'+value+'}';
      template_str=template_str.replace(new RegExp(pattern,'g'), values[value]);
    }
    return template_str;
  }

  $(document).on('lbbready', function () {
    initJobFormHandler();
    addLastSubmittedValue();
    disablePeamRecruiterFields();
  });

})(jQuery);

(function ($) {

  var FORM_STORAGE_KEY = "FORM_IDENTIFICATION_VALUES";

  // Save user data when submitting the identification form
  $('.identification-form').submit(function(e) {
    $form = $(e.target);

    var siret     = $form.find("input[name='siret']").val();
    var lastName  = $form.find("input[name='last_name']").val();
    var firstName = $form.find("input[name='first_name']").val();
    var phone     = $form.find("input[name='phone']").val();
    var email     = $form.find("input[name='email']").val();

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

      // Do not override last_name/first_name/email if data comes from PE Connect
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
  var jobRowTemplate = [
    '<tr id="{ROME}">',
      '<td><label>{LABEL}</label></td>',
      '<td class="text-center">',
        '<label>',
          '<input checked type="checkbox" name="extra_romes_to_add" value="{ROME}">',
        '</label>',
      '</td>',
      '<td class="text-center">',
        '<label>',
          '<input checked type="checkbox" name="extra_romes_alternance_to_add" value="{ROME}">',
        '</label>',
      '</td>',
    '</tr>',
  ].join('');

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
    if (alreadyExists) {
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

  $(':checkbox.js-check-all').on('click', function (e) {
    e.stopPropagation();
    var checkbox = $(this);
    var checkboxSate = checkbox.is(':checked');
    var targetCheckboxes = $("input[name='" + checkbox.data('target-input-name') + "']");
    targetCheckboxes.prop('checked', checkboxSate);
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
    addLastSubmittedValue();
    disablePeamRecruiterFields();
  });

})(jQuery);

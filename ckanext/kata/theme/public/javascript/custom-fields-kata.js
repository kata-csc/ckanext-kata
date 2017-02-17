/* Module for working with multiple custom field inputs. This will create
 * a new field when the user enters text into the last field key. It also
 * gives a visual indicator when fields are removed by disabling them.
 *
 * See the snippets/custom_form_fields.html for an example.
 */
this.ckan.module('custom-fields-kata', function (jQuery, _) {
  return {
    options: {
      /* The selector used for each custom field wrapper */
      fieldSelector: '.control-custom',
      numfields: 1,
      index: null,
      keep: null,
      hide: null,
      remove: null
    },

    /* Initializes the module and attaches custom event listeners. This
     * is called internally by ckan.module.initialize().
     *
     * Returns nothing.
     */
    initialize: function () {
      if (!jQuery('html').hasClass('ie7')) {
        jQuery.proxyAll(this, /_on/);

        var delegated = '#' + this.el[0].id + ' input:first';
        //this.el.on('change', delegated, this._onChange);
        this.el.on('change', ':checkbox.icon-plus-sign', this._onChange);

        // Style the remove checkbox like a button.
        //this.$('.checkbox').addClass("btn btn-danger icon-remove");

        // Create tooltips with no fade-in (change false to number for a fade-in)
        jQuery(".kata-plus-btn").tooltip({ show: false });
      }

      /* Show notification if user changes availability
       * from access_application_rems to something else.
       */
      $("#usage-info input:radio").change(function () {
        if ($(this).is(":checked") && $(this).attr('id') != 'access_application_rems') {
          if ($('#access_application_rems_identifier').val().match('^.+$') !== null) {
            $('#rems-pid-change-alert').css('display', 'block');
          }
        }
        $('#access_application_rems_identifier').val('');
        $('#access_application_rems_identifier').trigger('change');
      });

      /* Change external_id input value based on access_application_rems_identifier field. */
      $('#access_application_rems_identifier').change(function() {
        $('#external_id').val($(this).val());
      });
    },

    /* Creates a new field and appends it to the list. This currently works by
     * cloning and erasing an existing input rather than using a template. In
     * future using a template might be more appropriate.
     *
     * element - Another custom field element to wrap.
     *
     * Returns nothing.
     */
    newField: function (element) {
      var fields = this.cloneField(element);
      // Do some adjusting for copied PID fields
      fields.find('.pid').attr('readonly', false);
      $("#target").val($("#target option:first").val());
      fields.find('select.pid').val($('select.pid option:first').val());
      fields.find('select.pid option').removeProp('selected');

      fields.find('.pid').removeClass (function (index, css) {
        return (css.match (/(^|\s)pids_\S+/g) || []).join(' ');
      });

      // Remove tooltips
      fields.find('.form-instructions').remove();

      this.el.append(fields);
    },

    /* Clone the provided element and use resetField() on it.
     *
     * current - An element containing input fields, usually 'div'
     *
     * Return a newly created element.
     */
    cloneField: function (current) {
      return this.resetFields(jQuery(current).clone());
    },

    /* Wipe the contents and increment 'for', 'id' and 'name' attributes of the
     * input fields of the element 'field' provided (if possible).
     * Input field with attribute like name="smthng__hnghng__role" is not wiped.
     *
     * field - A element (like div) containing multiple input fields.
     *
     * Return the wiped element.
     */
    resetFields: function (field) {
      var numfields = this.options.numfields;
      var get_number = function (int) { return parseInt(int, 10) + numfields; };
      if (this.options.index) {
          numfields = parseInt($('#' + this.options.index).val());
          get_number = function (int) { return numfields; };
      }

      function increment(index, string) {
        return (string || '').replace(/\d+/, get_number);
      }

      var input = field.find(":input");
      input.attr('id', increment).attr('name', increment);
      input = input.not("[name*='role']")
      if (this.options.keep) {
        input = input.not("[name*='" + this.options.keep + "']");
      }
      input.val('')

      var label = field.find('label');
      label.text(increment).attr('for', increment);
      var checkboxes = field.find(':input[type="checkbox"]');
      checkboxes.hide();
      var buttons = field.find('button');
      buttons.hide();

      if (this.options.hide) {
        field.find(this.options.hide).hide();
      }

      if (this.options.remove) {
        field.find(this.options.remove).remove();
      }

      field.find("[data-module='autocomplete']").each(function(index, element) {
        $(element).show();
        ckan.module.initializeElement(element);
      });

      field.find(".kata-plus-btn").remove();

      return field;
    },

    /* Disables the provided field and input elements. Can be re-enabled by
     * passing false as the second argument.
     *
     * field   - The field to disable.
     * disable - If false re-enables the element.
     *
     * Returns nothing.
     */
    disableField: function (field, disable) {
      field.toggleClass('disabled', disable !== false);
      field.find(':input:not(:checkbox)').prop('disabled', disable !== false);
    },

    /* Event handler that fires when the last key in the custom field block
     * changes.
     */
    _onChange: function (event) {
      if (event.target.value !== '') {
        var parent = jQuery(event.target).parents('.control-custom');
        this.newField(parent);

        if (this.options.index) {
          var index = $('#' + this.options.index);
          index.val(parseInt(index.val()) + 1);
        } else {
          this.options.numfields += 1;
        }
      }
    },
    /* Event handler called when the remove checkbox is checked */
    _onRemove: function (event) {
      var parent = jQuery(event.target).parents('.control-custom');
      this.disableField(parent, event.target.checked);
    }
  };
});

KATA = function () {}

KATA.toggleAccess = function(obj) {
    /* Shows and hides data access inputs according to selection */
    switch (obj.id) {
        case 'access_application':
            $('#urlDiv_access_application').slideDown("fast");
            $('#urlDiv_access_request').slideUp("fast");
            $('#urlDiv_direct_download').slideUp("fast");
            $('#access_request').prop('checked', false);
            $('#contact_owner').prop('checked', false);
            $('#direct_download').prop('checked', false);
            break;
        case 'direct_download':
            $('#urlDiv_access_application').slideUp("fast");
            $('#urlDiv_access_request').slideUp("fast");
            $('#urlDiv_direct_download').slideDown("fast");
            $('#access_application').prop('checked', false);
            break;
        case 'access_request':
            $('#urlDiv_access_application').slideUp("fast");
            $('#urlDiv_access_request').slideDown("fast");
            $('#urlDiv_direct_download').slideUp("fast");
            $('#access_application').prop('checked', false);
            break;
        case 'contact_owner':
            $('#urlDiv_access_application').slideUp("fast");
            $('#urlDiv_access_request').slideUp("fast");
            $('#urlDiv_direct_download').slideUp("fast");
            $('#access_application').prop('checked', false);
            break;
        case 'access_application_rems':
            $('#access_application_rems_box').slideDown("fast");
            $('#access_application_other_box').slideUp("fast");
            break;
        case 'access_application_other':
            $('#access_application_other_box').slideDown("fast");
            $('#access_application_rems_box').slideUp("fast");
            break;
        }
};

KATA.checkLang = function(obj) {
    $('#langdiv').toggle();
    if ($(obj).val().length > 0 && !$('#langdiv').is(':visible')) {
        alert('Losing data on language if this is disabled!');
    }
};


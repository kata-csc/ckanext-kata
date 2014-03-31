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
      numfields: 1
    },

    /* Initializes the module and attaches custom event listeners. This
     * is called internally by ckan.module.initialize().
     *
     * Returns nothing.
     */
    initialize: function () {
      //if (!jQuery.browser.msie || !jQuery.browser.version == '7.0') {
        jQuery.proxyAll(this, /_on/);

        var delegated = '#' + this.el[0].id + ' input:first';
        //this.el.on('change', delegated, this._onChange);
        this.el.on('change', ':checkbox', this._onChange);

        // Style the remove checkbox like a button.
        //this.$('.checkbox').addClass("btn btn-danger icon-remove");
        
        // Create tooltips with no fade-in (change false to number for a fade-in)
        jQuery( ".kata-plus-btn" ).tooltip({ show: false });
      //}
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
      this.el.append(this.cloneField(element));
    },

    /* Clones the provided element, wipes it's content and increments it's
     * for, id and name fields (if possible).
     *
     * current - A custom field to clone.
     *
     * Returns a newly created custom field element.
     */
    cloneField: function (current) {
      return this.resetField(jQuery(current).clone());
    },

    /* Wipes the contents of the field provided and increments it's name, id
     * and for attributes.
     *
     * field - A custom field to wipe.
     *
     * Returns the wiped element.
     */
    resetField: function (field) {
      var numfields = this.options.numfields;
      function increment(index, string) {
        var str = (string || '').replace(/\d+/, function (int) { return parseInt(int, 10) + numfields; })
        return str;
      }

      var input = field.find(':input');
      input.val('').attr('id', increment).attr('name', increment);

      var label = field.find('label');
      label.text(increment).attr('for', increment);
      var checkboxes = field.find(':input[type="checkbox"]');
      checkboxes.hide();
      var buttons = field.find('button');
      buttons.hide();
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
        this.options.numfields += 1
      }
    },
    /* Event handler called when the remove checkbox is checked */
    _onRemove: function (event) {
      var parent = jQuery(event.target).parents('.control-custom');
      this.disableField(parent, event.target.checked);
    }
  };
});

KATA = function() {}
KATA.toggleAccess = function(obj) {
	/* Shows and hides data access inputs according to selection */
	switch (obj.id) {
		case 'access_application':
			$('#urlDiv_access_application').show();
			$('#urlDiv_access_request').hide();
			$('#urlDiv_direct_download').hide();
			break;
		case 'direct_download':
			$('#urlDiv_access_application').hide();
			$('#urlDiv_access_request').hide();
			$('#urlDiv_direct_download').show();
			break;
		case 'access_request':
			$('#urlDiv_access_application').hide();
			$('#urlDiv_access_request').show();
			$('#urlDiv_direct_download').hide();
			break;
		case 'contact_owner':
			$('#urlDiv_access_application').hide();
			$('#urlDiv_access_request').hide();
			$('#urlDiv_direct_download').hide();
			break;
		}
	}
KATA.checkLang = function(obj) {
	$('#langdiv').toggle();
	if ($(obj).val().length > 0 && !$('#langdiv').is(':visible')) {
		alert('Losing data on language if this is disabled!');
	}
}


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
      lastint: 1,
    },

    /* Initializes the module and attaches custom event listeners. This
     * is called internally by ckan.module.initialize().
     *
     * Returns nothing.
     */
    initialize: function () {
      if (!jQuery.browser.msie || !jQuery.browser.version == '7.0') {
        jQuery.proxyAll(this, /_on/);

        var delegated = '#' + this.el[0].id + ' input:first';
        //this.el.on('change', delegated, this._onChange);
        this.el.on('change', ':checkbox', this._onChange);

        // Style the remove checkbox like a button.
        //this.$('.checkbox').addClass("btn btn-danger icon-remove");
        
        // Create tooltips with no fade-in (change false to number for a fade-in)
        jQuery( document ).tooltip({ show: false });
      }
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
      var lastint = this.options.lastint;
      function increment(index, string) {
        var str = (string || '').replace(/\d+/, function (int) { return parseInt(int, 10) + lastint; })
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
        this.options.lastint += 1
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
	/* Shows and hides data access inputs according to selection, also juggles the accessURL input HTML code back and forth */
	switch (obj.id) {
		case 'form':
			$('#accessDiv').show();
			$('#urlDiv_ident').hide();
			$('#urlDiv_free').hide();
			break;
		case 'free':
			$('#accessDiv').hide();
			$('#urlDiv_ident').hide();
			$('#urlDiv_free').show();
			if ($('#urlDiv_ident').html().length > 10) {
				/* Consider length <= 10 as empty */
				$('#urlDiv_free').html($('#urlDiv_ident').html());
				$('#urlDiv_ident').html('');
			}
			break;
		case 'ident':
			$('#accessDiv').hide();
			$('#urlDiv_ident').show();
			$('#urlDiv_free').hide();
			if ($('#urlDiv_free').html().length > 10) {
				/* Consider length <= 10 as empty */
				$('#urlDiv_ident').html($('#urlDiv_free').html());
				$('#urlDiv_free').html('');
			}
			break;
		case 'contact':
			$('#accessDiv').hide();
			$('#urlDiv_ident').hide();
			$('#urlDiv_free').hide();
			break;
		}
	}
KATA.checkLang = function(obj) {
	$('#langdiv').toggle();
	if ($(obj).val().length > 0 && !$('#langdiv').is(':visible')) {
		alert('Losing data on language if this is disabled!');
	}
}

this.ckan.module('reqaccess', function($, _) {
	return {
		/* options object can be extended using data-module-* attributes */
		options : {
			id: null,
			action: null,
			loading: false,
			i18n: {
				follow: _('Request access'),
				unfollow: _('Already requested access')
			}
		},

		/* Initialises the module setting up elements and event listeners.
		 *
		 * Returns nothing.
		 */
		initialize: function () {
			$.proxyAll(this, /_on/);
			this.el.on('click', this._onClick);
		},

		/* Handles the clicking of the button
		 *
		 * event - An event object.
		 *
		 * Returns nothing.
		 */
		_onClick: function(event) {
			var options = this.options;
			if (
				options.id && !options.loading
			) {
				event.preventDefault();
				var client = this.sandbox.client;
				options.loading = true;
				path = 'reqaccess'
				this.el.addClass('disabled');
				client.call('POST', path, { id : options.id }, this._onClickLoaded);
			}
		},

		/* Fired after the call to the API to request access
		 *
		 * json - The return json from the follow / unfollow API call
		 *
		 * Returns nothing.
		 */
		_onClickLoaded: function(json) {
			var options = this.options;
			var sandbox = this.sandbox;
			options.loading = false;
			this.el.removeClass('disabled');
			console.log(json)
			if (json.result.ret == 'Yes') {
				this.el.html('<i class="icon-remove-sign"></i> ' + this.i18n('unfollow')).removeClass('btn-success').addClass('btn-danger');
			} else {
				this.el.html('<i class="icon-plus-sign"></i> ' + this.i18n('follow')).removeClass('btn-danger').addClass('btn-success');
			}
		}
	};
});


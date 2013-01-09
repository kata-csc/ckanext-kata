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
      var buttons = field.find('input[type="button"]');
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
      if (event.target.value !== '' && this._checklangs(event)) {
        var parent = jQuery(event.target).parents('.control-custom');
        this.newField(parent);
        this.options.lastint += 1
      }
    },
    _checklangs: function (event) {
        var langs = $('#lastlang input[type="text"]');
        var parent = jQuery(event.target).parents('.control-custom').parents('#lastlang');
        if (parent.length == 1) {
        var reserved = ['aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'ar', 'as', 'av', 'ay', 'az', 'ba', 'be', 'bg', 'bh', 'bi', 'bm', 'bn', 'bo', 'br', 'bs', 'ca', 'ce', 'ch', 'co', 'cr', 'cs', 'cu', 'cv', 'cy', 'da', 'de', 'dv', 'dz', 'ee', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'ff', 'fi', 'fj', 'fo', 'fr', 'fy', 'ga', 'gd', 'gl', 'gn', 'gu', 'gv', 'ha', 'he', 'hi', 'ho', 'hr', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'io', 'is', 'it', 'iu', 'ja', 'jv', 'ka', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko', 'kr', 'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lb', 'lg', 'li', 'ln', 'lo', 'lt', 'lu', 'lv', 'mg', 'mh', 'mi', 'mk', 'ml', 'mn', 'mo', 'mr', 'ms', 'mt', 'my', 'na', 'nb', 'nd', 'ne', 'ng', 'nl', 'nn', 'no', 'nr', 'nv', 'ny', 'oc', 'oj', 'om', 'or', 'os', 'pa', 'pi', 'pl', 'ps', 'pt', 'qu', 'rm', 'rn', 'ro', 'ru', 'rw', 'sa', 'sc', 'sd', 'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su', 'sv', 'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw', 'ty', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'wo', 'xh', 'yi', 'yo', 'za', 'zh', 'zu'];
        var tocheck = [];
        langs.each(function() {
             tocheck.push($(this));
        });
        return tocheck.length + 1 <= reserved.length;
        } else {
        return true;
        }
    },
    /* Event handler called when the remove checkbox is checked */
    _onRemove: function (event) {
      var parent = jQuery(event.target).parents('.control-custom');
      this.disableField(parent, event.target.checked);
    }
  };
});

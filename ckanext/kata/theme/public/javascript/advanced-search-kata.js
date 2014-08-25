/** Kata search form code
 */

this.ckan.module('advanced-search-kata', function (jQuery, _) {
  /** CKAN module to update input field name.
   */
  return {
    options: {
      target: 'select.kata-search-by'
    },

    initialize: function () {
      var _this = this;

      this.el.on('change', this.options.target, function () {
        temp_arr = this.id.split('-');
        index = temp_arr[temp_arr.length - 1];
        //console.log(index);
        jQuery( "#advanced-search-text-" + index ).attr('name', this.value + '-' + index);
      });
    }
  };
});

/*
 * Similar to select-switch in CKAN, but targets only the result order selector.
 */
this.ckan.module('select-switch-order-by', {

  options: {
    target: 'select#field-order-by'
  },

  initialize: function () {
    var _this = this;

    this.el.on('change', this.options.target, function () {
      _this.el.submit();
    });
  }
});

/*this.ckan.module('search-toggle', function (jQuery, _) {
  return {

    initialize: function () {
      var _this = this;

      this.el.on('click', function () {

        if (this.id == 'toggle_advanced') {
          jQuery('#content .advanced_search_toggled').show();
          jQuery('#content .basic_search_toggled').hide();
        } else {
          jQuery('#content .advanced_search_toggled').hide();
          jQuery('#content .basic_search_toggled').show();
        }

      });
    }
  };
});*/

/*
toggle_search = function(type) { */
/** Toggle visibility between basic and advanced search.
 */ /*
  if (type == 'advanced') {
    $('#content .advanced_search_toggled').show();
    $('#content .basic_search_toggled').hide();
  } else {
    $('#content .advanced_search_toggled').hide();
    $('#content .basic_search_toggled').show();
  }
} */


add_search_row = function(index) {
  /** Add a new row of search elements to advanced search page.
   */
  new_index = (index + 1);

  if (!$("#advanced-search-row-" + new_index).length) {

    // Clone a new element
    cloned_row = $("#advanced-search-row-0").clone(true);

    // Update indexes.
    cloned_row.attr('id', 'advanced-search-row-' + new_index);
    cloned_row.html(cloned_row.html().replace(/-\d+/g, '-' + new_index));

    // Replace field names with correct ones
    cloned_row.html(cloned_row.html().replace(/___/g, ''));

    // Make this visible
    cloned_row.attr('class', cloned_row.attr('class').replace('hidden', '').trim());
    //cloned_row.show();

    // Update element remove button
    cloned_row.children('a#del_search_element').attr('onclick', 'remove_search_row(' + new_index + ');');

    cloned_row.insertBefore($('div#search-fields-end'));
  }

  // Update element adding button
  $('a#new_search_element').attr('onclick', 'add_search_row(' + new_index + '); return false;');

}

remove_search_row = function(index) {
  /** Remove a row of search elements from advanced search page.
   */

  row_to_remove = $("#advanced-search-row-" + index);

  if (row_to_remove.length) {
    row_to_remove.remove();
  }

}
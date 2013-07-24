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


toggle_search = function(type) {
/** Toggle visibility between basic and advanced search.
 */
  if (type == 'advanced') {
    $('#content .advanced_search_toggled').show();
    $('#content .basic_search_toggled').hide();
  } else {
    $('#content .advanced_search_toggled').hide();
    $('#content .basic_search_toggled').show();
  }
}


add_search_elements = function(index) {
  /** Add a new row of search elements to advanced search page.
   */
  new_index = (index + 1);

  if (index == 1 && $("#advanced-search-row-" + new_index).is(":hidden")) {
    // Reveal a hidden element
    $("#advanced-search-row-" + new_index).show();
  } else {
    // Clone a new element
    added = false;

    while (!added) {

      if (!$("#advanced-search-row-" + new_index).length) {
        cloned_row = $("#advanced-search-row-" + index).clone(true);

        // Update indexes.

        cloned_row.attr('id', 'advanced-search-row-' + new_index);
        cloned_row.html(cloned_row.html().replace(/-\d+/g, '-' + new_index));

        cloned_row.insertBefore($('button#advanced_search_submit'));

        added = true;
      } else
        new_index++;

    }
  }

  // Update element adding button
  $('a#new_search_element').attr('onclick', 'add_search_elements(' + new_index + ');');

}
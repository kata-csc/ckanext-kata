/** Kata search form code
 */

this.ckan.module('advanced-search-kata', function (jQuery, _) {
  return {
    options: {
      target: 'select.kata-search-by'
    },

    initialize: function () {
      var _this = this;

      this.el.on('change', this.options.target, function () {
        temp_arr = this.id.split('-');
        index = temp_arr[temp_arr.length - 1];
        console.log(index);
        jQuery( "#advanced-search-text-" + index ).attr('name', this.value);
      });
    }
  };
});

this.ckan.module('search-toggle', function (jQuery, _) {
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
});

toggle_search = function(type) {
  if (type == 'advanced') {
    $('#content .advanced_search_toggled').show();
    $('#content .basic_search_toggled').hide();
  } else {
    $('#content .advanced_search_toggled').hide();
    $('#content .basic_search_toggled').show();
  }
}

add_search_elements = function(index) {
  if (!$("#advanced-search-row-" + (index + 1)).length) {
    cloned_row = $("#advanced-search-row-" + index).clone();

    //console.log($("#advanced-search-row-" + index));
    //cloned_row.html(cloned_row.html().replace('advanced-search-row-' + index, 'advanced-search-row-' + (index + 1)));
    cloned_row.html(cloned_row.html().replace('advanced-search-text-' + index, 'advanced-search-text-' + (index + 1)));
    cloned_row.html(cloned_row.html().replace('advanced-search-by-' + index, 'advanced-search-by-' + (index + 1)));
    cloned_row.html(cloned_row.html().replace('element-relation-' + index, 'element-relation-' + (index + 1)));
    cloned_row.html(cloned_row.html().replace('add_search_elements(' + index + ');', 'add_search_elements(' + (index + 1) + ');'));
    cloned_row.attr('id', 'advanced-search-row-' + (index + 1));

    cloned_row.insertAfter($("#advanced-search-row-" + index));
    //console.log('jees');
  }

}
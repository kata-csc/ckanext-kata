/** Kata search form code
 */

this.ckan.module('advanced-search-kata', function (jQuery, _) {
  return {
    options: {
      target: 'select'
    },

    initialize: function () {
      var _this = this;

      this.el.on('change', this.options.target, function () {
        jQuery( "#advanced-search-01-text" ).attr('name', this.value);
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
          jQuery('.advanced_search_toggled').show();
          jQuery('.basic_search_toggled').hide();
        } else {
          jQuery('.advanced_search_toggled').hide();
          jQuery('.basic_search_toggled').show();
        }

      });
    }
  };
});

toggle_search = function(type) {
  if (type == 'advanced') {
    $('.advanced_search_toggled').show();
    $('.basic_search_toggled').hide();
  } else {
    $('.advanced_search_toggled').hide();
    $('.basic_search_toggled').show();
  }

}
/** Kata search form code
 */

this.ckan.module('advanced-search-kata', function (jQuery, _) {

  options: {
    target: 'select'
  },

  initialize: function () {
    var _this = this;

    this.el.on('change', this.options.target, function () {
      //_this.el.submit();
      console.log(this);
    });
  }
});

this.ckan.module('kata-terms-of-use', function (jQuery, _) {
  return {
    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.on('change', this._onChange);
    },
    _onChange: function () {
      val = this.el.prop('checked') ? false : true;
      document.getElementsByName("save")[0].disabled = val;
      document.getElementsByName("save")[1].disabled = val;
    }
  };
});
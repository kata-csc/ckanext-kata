this.ckan.module('kata-save-tools', function (jQuery, _) {
  return {
    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
    },
    _onClick: function () {
      document.getElementById("private").value = "False";
    }
  };
});
this.ckan.module('kata-instructions', function (jQuery, _) {
  return {
    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
    },

    _onClick: function () {
      var h = (this.el[0].clientHeight == 120) ? 'auto' : '120px';
      this.el.css({ 'height': h});
    }
  };
});
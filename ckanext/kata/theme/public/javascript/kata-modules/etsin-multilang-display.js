this.ckan.module('etsin-multilang-display', function ($, translate) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/, /_activate/);
      this.tabs = this.el.find('li[data-value]');
      this.fields = this.el.find('.multilang-field');
      var currentlang = this.options.currentlang || 'en';
      if (currentlang === 'en') {
        currentlang = 'eng';
      } else if (currentlang === 'fi') {
        currentlang = 'fin';
      }
      this._activateTab(currentlang);

      this.tabs.on('click', this._onClick);
    },

    _activateTab: function (lang) {
      this.tabs.removeClass('active');
      var found = this.tabs.filter('[data-value="'+lang+'"]');
      if (found.length === 0) {
        found = this.tabs.eq(0);
        lang = found.data('value');
      }
      found.addClass('active');

      this.fields.addClass('hidden');
      this.fields.filter('[data-value="'+lang+'"]').removeClass('hidden');
    },

    _onClick: function (event) {
      var lang = $(event.target).closest('li').data('value');
      this._activateTab(lang);
    }
  };
});

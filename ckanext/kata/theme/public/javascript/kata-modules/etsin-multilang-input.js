this.ckan.module('etsin-multilang-input', function ($, translate) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/, /_activate/);
      this.tabs = this.el.find('li.multilang-tab');
      this.fields = this.el.find('.multilang-input');
      this.plustab = this.el.find('li.multilang-tab:first-child.adder');

      var currentlang = this.options.currentlang || 'en';
      if (currentlang === 'en') {
        currentlang = 'eng';
      } else if (currentlang === 'fi') {
        currentlang = 'fin';
      }

      console.log(currentlang);
      this._activateTab(currentlang);

      this.tabs.on('click', this._onClick);
      this.plustab.on('click', this._addTab);
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
      console.log('[data-value="'+lang+'"]');
      console.log('this.options="'+this.options.currentlang+'"');
      this.fields.filter('[data-value="'+lang+'"]').removeClass('hidden');
    },

    _onClick: function (event) {
      var lang = $(event.target).closest('li').data('value');
      this._activateTab(lang);
    },

    _addTab: function (event) {
      var lang = _selectLanguage();
      this._newTab(lang);
      this._activateTab(lang);
      this._addPlustab();
    },

    _selectLanguage: function () {

    }
  };
});

ckan.module('kata-multilang-field', function ($, translate) {
  return {
    initialize: function () {
      console.log('kata-multilang-field init', this.options.model);
      $.proxyAll(this, /_on/);
      $.proxyAll(this, /_set/);
      this.model = this.options.model || {};
      var value = '';
      this.inputField = this.el.find('#' + this.options.name);
      // hax the lang code 2->3
      var current = this.options.current;
      if (current === 'fi') current = 'fin';
      if (current === 'en') current = 'eng';
      // end hax
      if (!_.isEmpty(this.model)) {
        this._setValue(current);
        // set lang tabs
        var ulEl = this.el.find('.nav-tabs');
        _.each(_.keys(this.model), function (langcode) {
          ulEl.append('<li><a class="multilang-tab multilang-tab-' + langcode + '">' + langcode + '</a></li>');
        });
        ulEl.append('<li><a class="multilang-tab multilang-tab-addnew">+</a></li>');
        this._setActiveTab(current);
      }

      // bindings
      this.el.find('.multilang-tab').on('click', this._onTabClick);
      this.inputField.on('input change', this._onInputChange);
    },
    _setValue: function (langcode) {
      this.inputField.val(this.model[langcode] || '');
    },
    _setActiveTab: function (langcode, el) {
      if (!el) {
        el = this.el.find('.multilang-tab-' + langcode);
      }
      el.closest('ul').find('li').removeClass('active');
      el.closest('li').addClass('active');
      this.current = langcode;
    },
    _onTabClick: function (event) {
      var el = $(event.target);
      var tabId = el.attr('class').match(/multilang-tab-\w+/);
      if (!tabId) {
        return;
      }
      var langcode = _.last(tabId[0].split('-'));
      if (langcode === 'addnew') {
        $('#add-new-lang-modal').modal({});
        $('#add-new-lang-modal .btn-primary').on('click', this._onModalClose);
        return;
      }
      this._setActiveTab(langcode, el);
      this._setValue(langcode);
    },
    _onInputChange: function (event) {
      this.model[this.current] = $(event.target).val();
    },
    _onModalClose: function () {
      console.log("modal close");
    }
  };
});

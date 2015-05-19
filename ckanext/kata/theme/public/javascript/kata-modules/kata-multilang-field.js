ckan.module('kata-multilang-field', function ($, translate) {
  return {
    initialize: function () {
      this.selectors = {
        modal: '#add-new-lang-modal',
        modalvalue: '#tab-language-selection',
        tab: 'multilang-tab',
        tabregex: /multilang-tab-\w+/,
        inputarea: '.multilang-input-area'
      };
      $.proxyAll(this, /_add/, /_get/, /_set/, /_on/);
      this.model = _.isObject(this.options.model) ? this.options.model : {};

      this.inputDiv = this.el.find(this.selectors.inputarea);

      // hax the lang code alpha2->alpha3
      var current = this.options.current;
      if (current === 'fi') current = 'fin';
      if (current === 'en') current = 'eng';
      this.current = current;
      // end hax

      this._setTabs();
    },
    _getLangFromEl: function(event, tag) {
      var el = $(event.target);
      if (!el.eq(0).is(tag)) {
        el = el.closest(tag);
      }
      if (tag === 'a') {
        var tabId = el.attr('class').match(this.selectors.tabregex);
        if (!tabId) {
          return;
        }
        return _.last(tabId[0].split('-'));
      } else {
        return _.last(el.attr('id').split('_'));
      }
    },
    _setValues: function () {
      var model = this.model;
      var callback = this._onInputChange;
      this.inputDiv.find('input').each(function () {
        var input = $(this);
        var lang = _.last(input.attr('name').split('_'));
        input.val(model[lang]);
        input.on('input change', callback);
      });
    },
    _setDropdown: function (ulEl, lang) {
      function generateLangOption(code) {
        return '<li data-langcode="' + code + '"><a>' + KataLanguages.get(code, lang) + '</a></li>';
      }
      var otherLabel = lang === 'fi' ? 'Muu…' : 'Other…';
      ulEl.append('<li class="dropdown"><a class="' + this.selectors.tab + ' ' + this.selectors.tab +
        '-addnew dropdown-toggle" data-toggle="dropdown"><i class="icon-plus"></i></a>' +
        '<ul class="dropdown-menu addnew-options" role="menu">' +
        generateLangOption('fin') + generateLangOption('eng') + generateLangOption('swe') +
        '<li class="divider"></li><li data-langcode="other"><a>' + otherLabel + '</a></li>' +
        '</ul>' +
        '</li>');
        this.el.find('.addnew-options li').on('click', this._onMenuSelect);
    },
    _setTabs: function () {
      var ulEl = this.el.find('.nav-tabs');
      var lang = this.options.current;
      ulEl.empty();
      if (!_.isEmpty(this.model)) {
        var inputs = [];
        _.each(_.keys(this.model), function (langcode) {
          var closer = _.size(this.model) > 1 ? '<span class="langtab-close"><i class="icon-remove"></i></span>' : '';
          var liEl = '<li><a class="' + this.selectors.tab + ' ' + this.selectors.tab + '-' + langcode + '">' +
            KataLanguages.get(langcode, lang) + closer + '</a></li>';
          ulEl.append(liEl);
          var elId = this.options.name + '__0__' + langcode;
          var inputEl = '<div class="multilang-input-wrapper">' +
            '<input id="'+elId+'" type="text" name="'+elId+'" class="input-block-level" value="" placeholder="placeholder" />' +
            '</div>';
          inputs.push(inputEl);
        }, this);
        this.inputDiv.empty().append(inputs.join(''));
        this._setValues();
        this._setActiveTab(this.current);
      }
      this._setDropdown(ulEl, lang);
      this.el.find('.' + this.selectors.tab).on('click', this._onTabClick);
      this.el.find('.' + this.selectors.tab + ' .icon-remove').on('click', this._onLangRemove);
    },
    _onMenuSelect: function (event) {
      var langcode = $(event.target).closest('li').data('langcode');
      if (langcode === 'other') {
        this._onOtherSelected();
        return;
      }
      if (langcode) {
        this._addNewLanguage(langcode);
      }
    },
    _setActiveTab: function (langcode, el) {
      if (!el) {
        el = this.el.find('.' + this.selectors.tab + '-' + langcode);
      }
      el.closest('ul').find('li').removeClass('active');
      el.closest('li').addClass('active');
      this.current = langcode;
      this.inputDiv.find('input').each(function () {
        var input = $(this);
        var lang = _.last(input.attr('name').split('_'));
        input.closest('.multilang-input-wrapper')[lang === langcode ? 'removeClass' : 'addClass']('multilang-hidden');
      });
    },
    _onLangRemove: function (event) {
      var langcode = this._getLangFromEl(event, 'a');
      if (!langcode) {
        return;
      }
      if (_.has(this.model, langcode) && _.size(this.model) > 1) {
        delete this.model[langcode];
        if (!_.has(this.model, this.current)) {
          this.current = _.first(_.keys(this.model));
        }
        this._setTabs();
      }
    },
    _onOtherSelected: function () {
      $(this.selectors.modal).modal({});
      $(this.selectors.modal + ' .btn-primary').on('click', this._onModalClose);
    },
    _onTabClick: function (event) {
      var langcode = this._getLangFromEl(event, 'a');
      if (!langcode || langcode === 'addnew') {
        return;
      }
      this._setActiveTab(langcode);
    },
    _onInputChange: function (event) {
      var langcode = this._getLangFromEl(event, 'input');
      if (!langcode) {
        return;
      }
      this.model[langcode] = $(event.target).val();
    },
    _addNewLanguage: function (langcode) {
      this.model[langcode] = '';
      this.current = langcode;
      this._setTabs();
    },
    _onModalClose: function () {
      var newLang = $(this.selectors.modalvalue).val();
      var isValidChoice = !_.isEmpty(newLang);
      if (isValidChoice) {
        $(this.selectors.modal).modal('hide');
        this._addNewLanguage(newLang);
        $(this.selectors.modalvalue).select2('val', '');
      }
    }
  };
});

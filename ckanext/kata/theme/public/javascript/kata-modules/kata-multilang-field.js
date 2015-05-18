ckan.module('kata-multilang-field', function ($, translate) {
  return {
    initialize: function () {
      this.selectors = {
        modal: '#add-new-lang-modal',
        modalvalue: '#add-new-lang-modal-value',
        tab: 'multilang-tab',
        tabregex: /multilang-tab-\w+/,
        inputarea: '.multilang-input-area'
      };
      $.proxyAll(this, /_get/);
      $.proxyAll(this, /_set/);
      $.proxyAll(this, /_on/);
      this.model = _.isObject(this.options.model) ? this.options.model : {};
      console.log("model", this.options.model, this.model);

      this.inputDiv = this.el.find(this.selectors.inputarea);

      // hax the lang code 2->3
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
    _setTabs: function () {
      var ulEl = this.el.find('.nav-tabs');
      ulEl.empty();
      if (!_.isEmpty(this.model)) {
        // set lang tabs
        var inputs = [];
        _.each(_.keys(this.model), function (langcode) {
          var liEl = '<li><a class="' + this.selectors.tab + ' ' + this.selectors.tab + '-' + langcode + '">' +
            langcode + '<span class="langtab-close"><i class="icon-remove"></i></span></a></li>';
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
      ulEl.append('<li><a class="' + this.selectors.tab + ' ' + this.selectors.tab +
        '-addnew"><i class="icon-plus"></i></a></li>');
      this.el.find('.' + this.selectors.tab).on('click', this._onTabClick);
      this.el.find('.' + this.selectors.tab + ' .icon-remove').on('click', this._onLangRemove);
      this.el.find('.' + this.selectors.tab + ' .icon-plus').on('click', function (event) {
        // icon clicks are consumed somewhere?
        $(event.target).closest('a.multilang-tab').click();
      });
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
      if (_.has(this.model, langcode)) {
        if (this.current === langcode) {
          this.current = _.first(_.keys(this.model));
        }
        delete this.model[langcode];
        this._setTabs();
      }
    },
    _onTabClick: function (event) {
      var langcode = this._getLangFromEl(event, 'a');
      if (!langcode) {
        return;
      }
      if (langcode === 'addnew') {
        $(this.selectors.modal).modal({});
        $(this.selectors.modal + ' .btn-primary').on('click', this._onModalClose);
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
    _onModalClose: function () {
      var newLang = $(this.selectors.modalvalue).val();
      var isValidChoice = !_.isEmpty(newLang);
      if (isValidChoice) {
        $(this.selectors.modal).modal('hide');
        this.model[newLang] = '';
        this.current = newLang;
        this._setTabs();
        $(this.selectors.modalvalue).val('');
      }
    }
  };
});

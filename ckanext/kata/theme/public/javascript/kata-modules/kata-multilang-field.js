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

      this.values = _.isObject(this.options.values) ? this.options.values : {};

      // hax the lang code alpha2->alpha3
      var current = this.options.current;
      if (current === 'fi') current = 'fin';
      if (current === 'en') current = 'eng';
      this.current = current;
      // end hax

      this.model = this.values;
      this.model[this.current] = this.model[this.current] ? this.model[this.current] : '';
      this._setTabs();
      this._setDropdown();
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

    _onInputChange: function (event) {
      var langcode = this._getLangFromEl(event, 'input');
      if (!langcode) {
        return;
      }
      this.model[langcode] = $(event.target).val();
    },

    // TODO: Modify & use this (from autocomplete.js) to prevent [enter] in title input field to send form. Instead trigger [tab] key.
    /* Called when a key is pressed.  If the key is a comma we block it and
     * then simulate pressing return.
     *
     * Returns nothing.
     */
    _onKeydown: function (event) {
      if (event.which === 188) {
        event.preventDefault();
        setTimeout(function () {
          var e = jQuery.Event("keydown", { which: 13 });
          jQuery(event.target).trigger(e);
        }, 10);
      }
    },

    _setValues: function () {
      var model = this.model;
      var callback = this._onInputChange;
      this.inputDiv.find('input').each(function () {
        var input = $(this);
        var lang = _.last(input.attr('id').split('_'));
        input.val(model[lang]);
        input.on('change', callback);
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
        var lang = _.last(input.attr('id').split('_'));
        input.closest('.multilang-input')[lang === langcode ? 'removeClass' : 'addClass']('hidden');
      });
    },

    _addNewLanguage: function (langcode) {
      this.model[langcode] = '';
      this.current = langcode;
      this._setTabs();
    },

    _onNewAddLang: function () {
      var newLang = $('#tab-language-selection2').val();
      var isValidChoice = !_.isEmpty(newLang);
      if (isValidChoice) {
        //$(this.selectors.modal).modal('hide');
        this._addNewLanguage(newLang);
        // FIXME: don't clear existing title if existing language is chosen again
        $('#tab-language-selection2').select2('val', '');
      }
    },

    _setDropdown: function () {
    //_setDropdown: function (ulEl, lang) {
      //function generateLangOption(code) {
      //  return '<li data-langcode="' + code + '"><a>' + KataLanguages.get(code, lang) + '</a></li>';
      //}
      //var otherLabel = lang === 'fi' ? 'Muu…' : 'Other…';
      //ulEl.append('<li class="dropdown"><a class="' + this.selectors.tab + ' ' + this.selectors.tab +
      //  '-addnew dropdown-toggle" data-toggle="dropdown"><i class="icon-plus"></i></a>' +
      //  '<ul class="dropdown-menu addnew-options" role="menu">' +
      //  //generateLangOption('fin') + generateLangOption('eng') + generateLangOption('swe') +
      //  '<input id="tab-language-selection" data-module="kata-language-selection" data-module-current="' + lang + '" />' +
      //  '<li class="divider"></li><li data-langcode="other"><a>' + otherLabel + '</a></li>' +
      //  '</ul>' +
      //  '</li>');
      //  this.el.find('.addnew-options li').on('click', this._onMenuSelect);

      //$('.select2-container').select2({
      //$('.select2-input').select2({
      //$('.select2-drop').select2({
      //$('.select2-choise').select2({
      //$('.select2-search').select2({
      //  placeholder: "Select a state",
      //  allowClear: true
      //});
      this.el.find('.addnew-options li input').on('change click', this._onNewAddLang);
    },

    _onTabClick: function (event) {
      var langcode = this._getLangFromEl(event, 'a');
      if (!langcode || langcode === 'addnew') {
        return;
      }
      this._setActiveTab(langcode);
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

    _setTabs: function () {
      var ulEl = this.el.find('.nav-tabs');
      var liEls = this.el.find('.nav-tabs > li').not('.dropdown');
      var dropdown = this.el.find('.nav-tabs > li.dropdown');
      var lang = this.options.current;
      liEls.remove();
      if (!_.isEmpty(this.model)) {
        console.log('this.model: ' + _.keys(this.model));
        this.inputDiv.empty();
        _.each(_.keys(this.model), function (langcode, index) {

          var closer = _.size(this.model) > 1 ? '<span class="langtab-close"><i class="icon-remove"></i></span>' : '';

          var elLangId = this.options.name + '__' + index +'__lang';
          var liEl = $('<li>').append(
            $('<a>', {
              'class': this.selectors.tab + ' ' + this.selectors.tab + '-' + langcode,
              'name': elLangId,
              'id': elLangId + '_id',
              'id': elLangId + langcode,
              'value': langcode
            }).html(KataLanguages.get(langcode, lang) + closer)
          );
          dropdown.before(liEl);

          var elValueId = this.options.name + '__' + index +'__value';
          var inputEl = $('<div>', { 'class': 'multilang-input' });
          inputEl.append( $('<input>', {
            'id': elValueId + '_' + langcode,
            'type': 'text',
            'name': elValueId,
            'class': 'input-block-level',
            'placeholder': 'placeholder'
          }));
          this.inputDiv.append(inputEl);
        }, this);
        this._setValues();
        this._setActiveTab(this.current);
      }
      this.el.find('.' + this.selectors.tab).on('click', this._onTabClick);
      this.el.find('.' + this.selectors.tab + ' .icon-remove').on('click', this._onLangRemove);
    }

  };
});

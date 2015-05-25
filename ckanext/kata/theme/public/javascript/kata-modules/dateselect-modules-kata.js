/**
 * Temporal coverage wrapper for two kata-datetimepickers
 */
this.ckan.module('kata-temporal-coverage', function ($, _) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/, /_translate/);
            this.lang = this.options.currentlang || 'en';
            this.sandbox.subscribe('kata-datetimepicker-update', this._onDataUpdate);
            this.sandbox.subscribe('kata-datetimepicker-error', this._onError);
            this.model = {};
            this.hadError = {};
        },

        teardown: function () {
            this.sandbox.unsubscribe('kata-datetimepicker-update', this._onDataUpdate);
            this.sandbox.unsubscribe('kata-datetimepicker-error', this._onError);
        },

        _translateError: function (data) {
            var translations = {
              'begin': {fi: 'Alku', en: 'Begin'},
              'end': {fi: 'Loppu', en: 'End'},
              'validDate': {
                fi: 'Päivämäärä/aika ei ole kelvollinen',
                en: 'Date/time is not valid'
              },
              'range': {
                fi: 'Loppu pitää olla alun jälkeen',
                en: 'End must be after the starting time'
              }
            };
            var message = [];
            if (data.value !== 'range') {
              if (data.name.match(/_begin/)) {
                message.push(translations.begin[this.lang]);
              } else {
                message.push(translations.end[this.lang]);
              }
            }
            message.push(translations[data.value][this.lang]);
            return message.join(': ');
        },

        /**
         * Sets or clears error messages
         */
        _onError: function (data) {
            if (data.name.substr(0, 8) !== 'temporal') {
              return;
            }
            var el = this.el.find('.kata-datepicker-error');
            if (data.value === 'validDate') {
              this.model.isValid = !data.error;
            }
            if (!data.error) {
              el.empty();
              if (this.hadError[data.name+data.value]) {
                // If there are form errors from backend we can clear the
                // error notification once the specific field is fixed
                this.hadError[data.name+data.value] = false;
                this.el.find('.kata-medium-error').remove();
              }
            } else {
              this.hadError[data.name+data.value] = true;
              var message = this._translateError(data);
              var errorEl = $('<span class="error-block kata-medium-error">' + message + '</span>');
              el.empty().append(errorEl);
            }
        },

        /**
         * Called when data is updated via pubsub.
         * Validates date range and delegates min/max settings between widgets
         */
        _onDataUpdate: function (data) {
            if (!this.model.isValid || !data || !data.name) {
              return;
            }
            this.model[data.name] = data.value;
            var current = data.name;
            var other = '';
            var isBegin = false;
            if (data.name.match(/_begin/)) {
              isBegin = true;
              other = data.name.replace(/_begin/, '_end');
              this.sandbox.publish(other, {min: data.value});
            } else if (data.name.match(/_end/)) {
              other = data.name.replace(/_end/, '_begin');
              this.sandbox.publish(other, {max: data.value});
            }
            if (this.model[current] && this.model[other]) {
              var fn = isBegin ? 'isBefore' : 'isAfter';
              var date1 = moment(this.model[current]);
              var date2 = moment(this.model[other]);
              var isValid = date1.isSame(date2) || date1[fn](date2);
              this._onError({
                name: current,
                error: !isValid,
                value: 'range'
              });
            } else {
              this._onError({
                name: current,
                error: false,
                value: 'range'
              });
            }
        }
    };
});


/**
 * A combined date picker + optional time & timezone widget
 */
this.ckan.module('kata-datetimepicker', function ($, _) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/, /_build/, /_set/);
            this.lang = this.options.currentlang || 'en';
            this.elId = 'kata-datepicker-' + this.options.name;
            var parent = this.el.find('.kata-datetimepicker-parent');
            this._buildTimeInput(parent);
            this._buildDatepicker(parent);
            this._setInitialValue(this.options.value);
            this.sandbox.subscribe(this.options.name, this._onMinMaxChange);
        },

        teardown: function () {
            this.sandbox.unsubscribe(this.options.name, this._onMinMaxChange);
        },

        _buildDatepicker: function (parent) {
            this.model = {};
            var model = this.model;
            this.el.addClass('kata-datepicker-container');
            var container = $('<div class="input-append"></div>');
            var input = $('<input type="text" maxlength="10" class="form-control kata-datepicker-date" id="' + this.elId + '">');
            container.append(input);
            input.attr('placeholder', this.lang === 'fi' ? 'vvvv-kk-pp' : 'yyyy-mm-dd');
            input.prop('disabled', !!this.options.disabled);
            input.datepicker({
                language: this.lang,
                weekStart: 1,
                todayBtn: 'linked',
                format: 'yyyy-mm-dd',
                forceParse: false,
                showOnFocus: false
            }).on('show', function () {
              model.isOpen = true;
            }).on('hide', function () {
              // delay model update so the closing click doesn't open it again
              setTimeout(function () {
                model.isOpen = false;
              }, 200);
            });
            input.on('input change', this._onDateInput);
            var calendarIcon = $('<i class="icon-calendar"></i>');
            var addon = $('<span class="add-on"></span>');
            addon.append(calendarIcon);
            container.append(addon);
            parent.prepend(container);
            calendarIcon.on('click', function () {
              // only need to handle opening click, clicking outside of input closes the picker
              if (!model.isOpen) {
                input.datepicker('show');
              }
            });
            parent.append($('<input type="hidden" id="' + this.options.name + '" name="' + this.options.name + '">'));
        },

        _buildTimeInput: function (parent) {
            var checkboxId = this.elId + '-check';
            var checkboxLabel = this.lang === 'fi' ? 'käytä tarkkaa kellonaikaa' : 'use exact time';
            var enabler = $('<label class="checkbox kata-datepicker-enabler"><input id="' + checkboxId +
                '" type="checkbox">' + checkboxLabel + '</label>');
            var timeEl = $('<input type="text" maxlength="8" placeholder="hh:mm:ss" class="form-control kata-datepicker-time">');
            // TODO: could use moment timezone...
            // hardcoded list makes it easy to use same thing as model and display value
            var timezoneList = ['-12:00', '-11:00', '-10:00', '-09:30', '-09:00', '-08:00', '-07:00', '-06:00', '-05:00', '-04:30', '-04:00', '-03:30', '-03:00', '-02:00', '-01:00', 'Z',
                      '+01:00', '+02:00', '+03:00', '+03:30', '+04:00', '+04:30', '+05:00', '+05:30', '+05:45', '+06:00', '+06:30', '+07:00', '+08:00', '+08:45', '+09:00', '+09:30',
                      '+10:00', '+10:30', '+11:00', '+11:30', '+12:00', '+12:45', '+13:00', '+14:00'];
            var tzId = this.elId + '-tz';
            var tz = $('<select class="form-control kata-datepicker-tz" id="' + tzId + '"></select>');
            var opts = [];
            $.each(timezoneList, function (index, item) {
                opts.push('<option value="' + item + '">' + item + '</option>');
            });
            tz.append($(opts.join(''))).val('Z');
            var details = $('<span class="time-details"></span>');
            parent.prepend(enabler);
            parent.prepend(details);
            details.append(timeEl);
            timeEl.attr('placeholder', 'hh:mm:ss');
            timeEl.on('input change', this._onTimeInput);
            details.append(tz);
            this.el.find('#' + checkboxId).on('click', this._onCheckboxChange);
            // initial state of time fields
            this.el.find('.time-details').hide();
            this.el.find('select').on('change', this._onTimezoneChange);
        },

        _onDateInput: function (event) {
          this.model.date = $(event.target).val();
          this._setIsoDatetimeField();
        },

        _onTimeInput: function (event) {
          this.model.time = $(event.target).val();
          this._setIsoDatetimeField();
        },

        _onTimezoneChange: function (event) {
          this.model.tz = $(event.target).val();
          this._setIsoDatetimeField();
        },

        /**
         * Validates the datetime as ISO 8601
         */
        _validate: function (datetime) {
          if (datetime === '') {
            // Empty is valid (should depend on field being mandatory...)
            return true;
          }
          // First validate the format so it's as expected
          var pattern = /^\d{4}(-\d{2}(-\d{2}(T\d{2}(:\d{2}(:\d{2})?)?(Z|[+-]\d{2}:\d{2})?)?)?)?$/;
          if (!datetime.match(pattern)) {
            return false;
          }
          // Then ensure that it is recognized as a valid time
          return moment(datetime).isValid();
        },

        /**
         * Sets the hidden form field value
         */
        _setIsoDatetimeField: function () {
          var combined = this.model.date ? this.model.date : '';
          if (this.model.useTime && combined) {
            combined += ('T' + (this.model.time || '00:00:00') + (this.model.tz || 'Z'));
          }
          var isValid = this._validate(combined);
          this.sandbox.publish('kata-datetimepicker-error', {
            name: this.options.name,
            error: !isValid,
            value: 'validDate'
          });
          this.el.find('#' + this.options.name).val(combined);
          this.sandbox.publish('kata-datetimepicker-update', {name: this.options.name, value: combined});
        },

        /**
         * Called when the time part toggler is clicked
         */
        _onCheckboxChange: function (event) {
          var checked = $(event.target).prop('checked');
          this.model.useTime = checked;
          this.el.find('.time-details')[checked ? 'show' : 'hide']();
          this._setIsoDatetimeField();
        },

        /**
         * Sets the model value from data-module-value
         * or uses "now" time if data-module-defaultnow is true
         */
        _setInitialValue: function (value) {
            if (!value || typeof value !== 'string') {
              if (!this.options.defaultnow) {
                return;
              }
              value = moment().format('YYYY-MM-DDTHH:mm:ssZ');
            }
            var dateField = this.el.find('#' + this.elId);
            var checkbox = this.el.find('#' + this.elId + '-check');
            var timeField = this.el.find('.kata-datepicker-time');
            var timezoneField = this.el.find('.kata-datepicker-tz');
            var parts = value.match(/^([^T]+)(T([0-9:]+)(Z|[-+0-9:]+)?)?$/);
            this.model.date = parts[1] || '';
            this.model.time = parts[3] || '';
            this.model.tz = parts[4] || 'Z';
            this.model.useTime = !!parts[2];
            dateField.val(this.model.date);
            if (this.model.useTime) {
              checkbox.prop('checked', true);
              this._onCheckboxChange({target: checkbox});
              timeField.val(this.model.time);
              timezoneField.val(this.model.tz);
            }
            this._setIsoDatetimeField();
        },

        /**
         * Called when min/max date should be adjusted on the picker
         */
        _onMinMaxChange: function (data) {
            if (!data && !(data.min || data.max)) {
              return;
            }
            var value = data.max ? data.max : data.min;
            if (value) {
              // only take the date part + fill out if it's partial
              value = value.substr(0, 10);
              while (value.length < 10) {
                value += '-01';
              }
            }
            var fn = data.hasOwnProperty('max') ? 'setEndDate' : 'setStartDate';
            this.el.find('#' + this.elId).datepicker(fn, value || false);
        }
    };
});

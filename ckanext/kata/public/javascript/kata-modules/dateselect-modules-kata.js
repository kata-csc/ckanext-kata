this.ckan.module('dateselect-simple-kata', function (jQuery, _)
{
  return {
    initialize: function () {
        var lm = $('#last_modified');
        lm.datetimepicker({
        timeFormat: "HH:mm:ssz",
        separator: 'T',
        dateFormat: "yy-mm-dd",
        showTimezone: true,
        showSecond: true,
        });
        var parsed = $.datepicker.parseDateTime("yy-mm-dd", "HH:mm:ssz", lm[0].value, {separator: 'T'}, {separator: 'T'} );
        if (parsed) {
        	lm.datetimepicker('setDate', (parsed));
        }
     },
  }
});
this.ckan.module('dateselect-dcmi-kata', function (jQuery, _)
{
  return {
  initialize: function () {
        var tcb = $('#temporal_coverage_begin');
        var tce = $('#temporal_coverage_end');
        tcb.datetimepicker({
        timeFormat: "HH:mm:ssz",
        separator: 'T',
        dateFormat: "yy-mm-dd",
        showTimezone: true,
        showSecond: true,
		onClose: function(dateText, inst) {
			if (tce.val() != '') {
				var testStartDate = tcb.datetimepicker('getDate');
				var testEndDate = tce.datetimepicker('getDate');
				if (testStartDate > testEndDate)
					tce.datetimepicker('setDate', testStartDate);
			}
			else {
				tce.val(dateText);
			}
		},
		onSelect: function (selectedDateTime){
			tce.datetimepicker('option', 'minDate', tcb.datetimepicker('getDate') );
		}
        });
        var parsed = $.datepicker.parseDateTime("yy-mm-dd", "HH:mm:ssz", tcb[0].value, {separator: 'T'}, {separator: 'T'} );
        if (parsed) {
        	tcb.datetimepicker('setDate', (parsed));
        }
        tce.datetimepicker({
        timeFormat: "HH:mm:ssz",
        separator: 'T',
        dateFormat: "yy-mm-dd",
        showTimezone: true,
        showSecond: true,
        onClose: function(dateText, inst) {
			if (tcb.val() != '') {
				var testStartDate = tcb.datetimepicker('getDate');
				var testEndDate = tce.datetimepicker('getDate');
				if (testStartDate > testEndDate)
					tcb.datetimepicker('setDate', testEndDate);
			}
			else {
				tcb.val(dateText);
			}
			},
			onSelect: function (selectedDateTime){
				tcb.datetimepicker('option', 'maxDate', tce.datetimepicker('getDate') );
			}
        });
        var parsed = $.datepicker.parseDateTime("yy-mm-dd", "HH:mm:ssz", tce[0].value, {separator: 'T'}, {separator: 'T'} );
        if (parsed) {
        	tce.datetimepicker('setDate', (parsed));
        }
     },
  }
});
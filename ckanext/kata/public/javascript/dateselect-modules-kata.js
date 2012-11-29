this.ckan.module('dateselect-simple-kata', function (jQuery, _)
{
  return {
    initialize: function () {
        var lm = $('#last_modified');
        lm.datetimepicker({
        timeFormat: "HH:mm:ssz",
        separator: '',
        dateFormat: "yy-mm-ddT",
        showTimezone: true,
        });
        var parsed = $.datepicker.parseDateTime("yy-mm-ddTHH:mm:ss", lm[0].value );
        if (parsed) {
        	lm.datetimepicker('setDate', (parsed));
        }
        var tc = $('#temporal_coverage');
        tc.datetimepicker({
        timeFormat: "HH:mm:ssz",
        separator: '',
        dateFormat: "yy-mm-ddT",
        showTimezone: true,
        });
     },
  }
});
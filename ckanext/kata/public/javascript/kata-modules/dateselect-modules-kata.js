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
  return {}
});
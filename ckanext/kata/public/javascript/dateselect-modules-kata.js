this.ckan.module('dateselect-simple-kata', function (jQuery, _)
{
  return {
    initialize: function () {
        $('#last_modified').datetimepicker({
        timeFormat: "HH:mm:ss",
        separator: '',
        dateFormat: "yy-mm-ddT",
        });
     },
  }
});
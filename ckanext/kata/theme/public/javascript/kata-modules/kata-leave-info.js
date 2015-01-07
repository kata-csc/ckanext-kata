
this.ckan.module('kata-leave-info', function (jQuery, _) {
  return {
    options: {
      message: "You have unsaved changes. Make sure to click 'Save Changes' below before leaving this page."
    },

    initialize: function () {
      var message = this.options.message;
      window.onbeforeunload = function () {
        return message;
      };
    }
  };
});

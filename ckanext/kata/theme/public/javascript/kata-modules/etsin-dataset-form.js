this.ckan.module('etsin-dataset-form', function ($, translate) {
  return {

    initialize: function () {
      $.proxyAll(this, /select/);

      var selectTab = this.selectTab;
      setTimeout(function () {
        selectTab(0);
      }, 200);

      $('#cancel-edit').click(function() {
        var newUrl = window.location.href;
        if(window.location.href.indexOf('/new') > -1) {
          newUrl = window.location.href.replace('/new', '');
        } else {
          newUrl = window.location.href.replace('/edit', '');
        }
        window.location.href = newUrl;
        return false;
      });
    },

    selectTab: function (index, force) {
      if (force || this.el.find('.dataset-tabs li.active').length === 0) {
        this.el.find('.dataset-tabs .dataset-tab').eq(0).click();
      }
    }
  };
});

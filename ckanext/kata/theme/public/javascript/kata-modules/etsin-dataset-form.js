this.ckan.module('etsin-dataset-form', function ($, translate) {
  return {

    initialize: function () {
      $.proxyAll(this, /select/);

      var selectTab = this.selectTab;
      setTimeout(function () {
        selectTab(0);
      }, 200);
    },

    selectTab: function (index, force) {
      if (force || this.el.find('.dataset-tabs li.active').length === 0) {
        this.el.find('.dataset-tabs .dataset-tab').eq(0).click();
      }
    }
  };
});

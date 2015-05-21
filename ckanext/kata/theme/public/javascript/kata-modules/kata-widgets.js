
this.ckan.module('kata-accordion', function ($, _) {
  return {
    initialize: function () {
      this.el.addClass('kata-accordion');

      // show the first one by default
      var el = this.el;
      var collapses = el.find('.collapse');
      collapses.collapse({toggle: false});
      collapses.eq(0).collapse('show');

      // fix style for the rest so the chevrons are shown correctly
      el.find('.accordion-toggle:gt(0)').addClass('collapsed');
    }
  };
});

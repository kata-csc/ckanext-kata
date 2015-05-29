
this.ckan.module('kata-accordion', function ($, _) {
  return {
    initialize: function () {
      this.el.addClass('kata-accordion');

      // try to open the correct collapse according to UI language
      var index = this.el.find('.lang-' + (this.options.currentlang === 'en' ? 'eng' : 'fin')).index();
      if (index < 0) {
        // if no match, just open the first one
        index = 0;
      }
      var el = this.el;
      var collapses = el.find('.collapse');
      collapses.collapse({toggle: false});
      collapses.eq(index).collapse('show');

      // fix style for the rest so the chevrons are shown correctly
      el.find('.accordion-toggle:lt(' + index + ')').addClass('collapsed');
      el.find('.accordion-toggle:gt(' + index + ')').addClass('collapsed');
    }
  };
});

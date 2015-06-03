
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


this.ckan.module('kata-facet-accordion', function ($, translate) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/, /_bind/);

      var el = this.el;
      var collapses = el.find('.collapse');
      collapses.collapse({toggle: false});
      el.find('.accordion-toggle').addClass('collapsed');

      var data = this.options.facets;
      if (!data) {
        return;
      }

      // Open the facet accordion if any facet choices are active
      var limitsChanged = _.any(_.values(data.search));
      var shouldBeOpen = _.any(data.fields) || limitsChanged;
      if (shouldBeOpen) {
        collapses.eq(0).collapse('show');
      }

      // Setup a toggler for the additional facets not shown initially
      setTimeout(this._bindCollapses, 200);
    },

    _onToggle: function () {
      this.el.find('.etsin-facet-list.collapse').collapse('toggle');
    },

    _bindCollapses: function () {
      var collapses = this.el.find('.etsin-facet-list.collapse');
      collapses.collapse();
      var toggler = this.el.find('#etsin-facet-list-toggle');
      toggler.on('click', this._onToggle);
    }
  };
});

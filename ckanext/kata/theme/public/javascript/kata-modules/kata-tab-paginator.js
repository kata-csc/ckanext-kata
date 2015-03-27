this.ckan.module('kata-tab-paginator', function (jQuery, _) {
  return {
    initialize: function () {

      // .times(n) multiplies the string nfold
      String.prototype.times = function(n) {
        return Array.prototype.join.call({length: n+1}, this);
      };

      var tabs = jQuery(".kata-dataset-tabs").children();
      var activeTabIdx = 0;

      //var undoneIndicator = "<span class='icon-ok-sign style='color:gray'></span>";
      //var activeIndicator = "<span class='icon-ok-sign' style='color:blue'></span>";

      var undoneIndicator = "<span class='empty-dot'></span>";
      var activeIndicator = "<span class='filled-dot'></span>";

       /* Progress indicator initialization */
      jQuery("#tab-indicator").append(activeIndicator);
      jQuery("#tab-indicator").append(undoneIndicator.times(tabs.length-1));

      jQuery("#prev-tab").prop('disabled', true);
      jQuery("#tab-indicator").prop('disabled', true);

      // show the indicator when all the items are loaded.
      jQuery("#tab-indicator").show();

      /* 'Previous Tab' and 'Next Tab' Button logic */
      jQuery('#next-tab').click(function(e){
        jQuery('.nav-tabs > .active').next('li').find('a').trigger('click');
        $("html, body").animate({scrollTop: $(".kata-dataset-tabs").offset().top - 10}, "fast");
      });

      jQuery('#prev-tab').click(function(e){
        jQuery('.nav-tabs > .active').prev('li').find('a').trigger('click');
        $("html, body").animate({scrollTop: $(".kata-dataset-tabs").offset().top - 10}, "fast");
      });

      /* update the paginator with progress indicator on 'tab shown' event */
      $('a[data-toggle="tab"]').on('shown', function (e) {

        /* generate the progress bar */
        activeTabIdx = $(e.target).closest('li').index();

        jQuery("#tab-indicator").empty();

        // generate a new one according to the index of the active tab
        jQuery("#tab-indicator").append(undoneIndicator.times(activeTabIdx));
        jQuery("#tab-indicator").append(activeIndicator);
        jQuery("#tab-indicator").append(undoneIndicator.times(tabs.length-activeTabIdx-1));

        /* enable/disable 'previous tab' and 'next tab' buttons according to active tab idx */
        if (activeTabIdx == 0) {
          $("#next-tab").prop('disabled', false);
          $("#prev-tab").prop('disabled', true);
        }
        else if (activeTabIdx+1 == tabs.length) {
          $("#prev-tab").prop('disabled', false);
          $("#next-tab").prop('disabled', true);
        }
        else {
          $("#prev-tab").prop('disabled', false);
          $("#next-tab").prop('disabled', false);
        }

      })

    }
  };
});
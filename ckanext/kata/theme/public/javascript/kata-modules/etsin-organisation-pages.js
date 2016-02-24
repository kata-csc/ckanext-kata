ckan.module('etsin-organisation-pages', function ($, _) {
    return {

        initialize: function () {
          var showTxt = "Show organization info";
          var hideTxt = "Hide organization info";
          var orgInfoBtn = $("#org-info-btn");
          var orgInfoFrame = $("#org-info-frame")
          orgInfoBtn.text(showTxt);

          orgInfoBtn.click(function() {
              if($(this).text() === showTxt) {
                  if(orgInfoFrame.not(":visible")) {
                      orgInfoFrame.show("slow");
                      $(this).text(hideTxt);
                  }
              } else if($(this).text() === hideTxt) {
                  if(orgInfoFrame.is(":visible")) {
                      orgInfoFrame.hide("slow");
                      $(this).text(showTxt);
                  }
              }

          });
          orgInfoFrame.mouseleave(function() {
              $(this).hide("slow");
              orgInfoBtn.text(showTxt);
          });
        }
    }
});
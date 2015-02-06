this.ckan.module('kata-autofill-by-id', function (jQuery, _) {
    return {

    initialize: function () {
        jQuery.proxyAll(this, /_on/);
        this.el.on('click', this._onClick);
    },

    _onClick: function () {

        var jqfrom = '[name="' + this.options.from + '"]';
        var jqto = '[name="' + this.options.to + '"]';
        var orcid = jQuery(jqfrom).val();
        var parts  = this.options.source.split('?');
        var end    = parts.pop();
        var source = parts.join('?') + encodeURIComponent(orcid) + end;
        var target = this.options.to;

        if (orcid.length > 0) {
            //Todo: replace classes with ajaxStart()? This messing with classes must be resolved when leaving proto type
            jQuery(jqto).parent().parent().addClass("alert-info");
            jQuery.getJSON(source, function(result) {
                jQuery.each(result, function(i, field) {
                    try {
                        if (field["first-name"].length < 1 && field["family-name"].length < 1) {
                            jQuery(jqto).parent().parent().addClass("alert-error");
                            jQuery(jqto).parent().parent().removeClass("alert-info");
                        }
                        else {
                            jQuery(jqto).val(field["first-name"] + " " + field["family-name"]);
                            jQuery(jqto).parent().parent().removeClass("alert-info");
                            if (jQuery(jqfrom).parent().parent().hasClass("alert-error")) {
                                jQuery(jqfrom).parent().parent().removeClass("alert-error");
                            }
                        }
                    }
                    catch(err) {
                        jQuery(jqfrom).parent().parent().addClass("alert-error");
                        jQuery(jqto).parent().parent().removeClass("alert-info");
                    }
                });
            });
        }
        else {
            jQuery(jqfrom).parent().parent().addClass("alert-error");
        }
    }
  };
});
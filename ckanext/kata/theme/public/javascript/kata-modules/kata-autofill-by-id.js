this.ckan.module('kata-autofill-by-id', function (jQuery, _) {
  return {

    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.on('change', this._onChange);
    },

    _onChange: function () {
      var from = this.options.from;
      var orcid = document.getElementsByName(from)[0].value;
      var parts  = this.options.source.split('?');
      var end    = parts.pop();
      var source = parts.join('?') + encodeURIComponent(orcid) + end;
      var target = this.options.to;
      if (orcid.length > 0) {
        jQuery.getJSON(source, function(result) {
          jQuery.each(result, function(i, field) {
            var elem = document.getElementsByName(target)[0];
            try {
              elem.value = field["first-name"] + " " + field["family-name"];
            }
            catch(err) {
              elem.style.color = "red";
              //document.getElementsByName(this.options.from)[0].borderColor = "red";
            }
          });
        });
      }
      else {
        document.getElementsByName(this.options.from)[0].className = "error-block";
      }
    }
  };
});
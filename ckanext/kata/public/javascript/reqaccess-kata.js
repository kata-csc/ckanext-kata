/** Dataset access request code from Nomovok
 *
 */

this.ckan.module('reqaccess', function($, _) {
    return {
        /* options object can be extended using data-module-* attributes */
        options : {
            id: null,
            action: null,
            loading: false,
            i18n: {
                follow: _('Request access'),
                unfollow: _('Already requested access')
            }
        },

        /* Initialises the module setting up elements and event listeners.
         *
         * Returns nothing.
         */
        initialize: function () {
            $.proxyAll(this, /_on/);
            this.el.on('click', this._onClick);
        },

        /* Handles the clicking of the button
         *
         * event - An event object.
         *
         * Returns nothing.
         */
        _onClick: function(event) {
            var options = this.options;
            if (
                options.id && !options.loading
                ) {
                event.preventDefault();
                var client = this.sandbox.client;
                options.loading = true;
                path = 'reqaccess'
                this.el.addClass('disabled');
                client.call('POST', path, { id : options.id }, this._onClickLoaded);
            }
        },

        /* Fired after the call to the API to request access
         *
         * json - The return json from the follow / unfollow API call
         *
         * Returns nothing.
         */
        _onClickLoaded: function(json) {
            var options = this.options;
            var sandbox = this.sandbox;
            options.loading = false;
            this.el.removeClass('disabled');
            console.log(json)
            if (json.result.ret == 'Yes') {
                this.el.html('<i class="icon-remove-sign"></i> ' + this.i18n('unfollow')).removeClass('btn-success').addClass('btn-danger');
            } else {
                this.el.html('<i class="icon-plus-sign"></i> ' + this.i18n('follow')).removeClass('btn-danger').addClass('btn-success');
            }
        }
    };
});


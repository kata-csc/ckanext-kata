/**
 * Created by jmlehtin on 6/11/2015.
 */

ckan.module('etsin-ida-prefill', function ($, _) {
    return {
        options: {
            i18n: {
                cancel: _('Cancel'),
                ok: _('OK')
            }
        },

        initialize: function () {
            var directDlField = $('#direct_download_URL');
            var idaPrefillModal = null;
            var idaUrnInput = $('#ida-prefill-input');
            var tips = $('#ida-modal-tips');
            var idaPidRegex = /^urn:nbn:fi:csc-ida.*s$/;

            checkRegexp = function(obj, regexp) {
                if(!(regexp.test(obj.val()))) {
                    obj.addClass('ui-state-error');
                    updateModalTips();
                    return false;
                } else {
                    return true;
                }
            }

            updateModalTips = function() {
                tips.removeClass('hide');
                tips.addClass('ui-state-highlight');
                setTimeout(function() {
                    tips.removeClass('ui-state-highlight', 1500);
                }, 500);
            }

            validateAndUpdate = function () {
                // Validate input fields
                var valid = true;
                tips.addClass("hide");
                idaUrnInput.removeClass('ui-state-error');
                valid = checkRegexp(idaUrnInput, idaPidRegex);

                if (valid) {
                    directDlField.val('https://avaa.tdata.fi/openida/dl.jsp?pid='.concat(idaUrnInput.val()));
                    idaPrefillModal.dialog('close');
                }
                return valid;
            }

            idaPrefillModal = $('#ida-prefill-modal').dialog({
                dialogClass: 'ida-dialog',
                autoOpen: false,
                height: 'auto',
                width: 600,
                modal: true,
                closeOnEscape: true,
                draggable: true,
                resizable: false,
                buttons: [
                    {
                        text: this.i18n('ok'),
                        click: function() {validateAndUpdate()},
                        type: 'submit'
                    },
                    {
                        text: this.i18n('cancel'),
                        click: function () {
                            $(this).dialog('close');
                        }
                    }
                ],
                close: function () {
                    idaUrnInput.removeClass('ui-state-error');
                },
                create:function () {
                    $(this).closest(".ui-dialog")
                        .find(".ui-button:first") // the first button
                        .addClass("btn btn-default");
                    $(this).closest(".ui-dialog")
                        .find(".ui-button") // the second button
                        .eq(1)
                        .addClass("btn btn-default");
                }
            });

            openIdaPopup = function () {
                idaPrefillModal.dialog('open');
            }

            idaUrnInput.on('input', function() {
                $('#ida-preview-url').text('IDA URL: https://avaa.tdata.fi/openida/dl.jsp?pid='.concat(idaUrnInput.val()))
            });
        }
    }
});

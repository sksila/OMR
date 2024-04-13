odoo.define('apco.DocumentsInspector', function (require) {
'use strict';

const DocumentsInspector = require('documents.DocumentsInspector');
const rpc = require('web.rpc');

console.log('onlyoffice open');

DocumentsInspector.include({
    events: _.extend({}, DocumentsInspector.prototype.events, {
        'click .o_inspector_onlyoffice': '_onlyOffice',
    }),
    
    _onlyOffice: function () {
        rpc.query({
            model: 'documents.document',
            method: 'get_only_office_url',
            args: [this.records[0].res_id],
        })
        .then(function (url) {
            window.open(url);
        })
    },
});

});

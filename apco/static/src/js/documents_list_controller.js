odoo.define("apco.DocumentsListController", function (require) {
    "use strict";

    console.log('test list');

    const DocumentsListController = require("spreadsheet.DocumentsListController");
    const DocumentsControllerMixin = require("documents.controllerMixin");
    const DocumentsApcoControllerMixin = require("apco.DocumentsControllerMixin");

    const ApcoListController = DocumentsListController.extend(
        DocumentsApcoControllerMixin,
        {
            events: Object.assign(
                {},
                DocumentsListController.prototype.events,
                DocumentsApcoControllerMixin.events,
                DocumentsControllerMixin.events
            ),
            custom_events: Object.assign(
                {},
                DocumentsListController.prototype.custom_events,
                DocumentsApcoControllerMixin.custom_events,
                DocumentsControllerMixin.custom_events
            ),

            /**
             * @override
             */
            updateButtons() {
                console.log('button list');
                this._super(...arguments);
                DocumentsControllerMixin.updateButtons.apply(this, arguments);
                DocumentsApcoControllerMixin.updateButtons.apply(this, arguments);
            },
        }
    );
    return ApcoListController;
});

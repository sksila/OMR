odoo.define("apco.KanbanController", function (require) {
    "use strict";

    console.log('test kanban');

    const DocumentsKanbanController = require("documents_spreadsheet.KanbanController");
    const DocumentsControllerMixin = require("documents.controllerMixin");
    const DocumentsApcoControllerMixin = require("apco.DocumentsControllerMixin");

    const ApcoKanbanController = DocumentsKanbanController.extend(
        DocumentsApcoControllerMixin,
        {
            events: Object.assign(
                {},
                DocumentsKanbanController.prototype.events,
                DocumentsApcoControllerMixin.events,
                DocumentsControllerMixin.events
            ),
            custom_events: Object.assign(
                {},
                DocumentsKanbanController.prototype.custom_events,
                DocumentsApcoControllerMixin.custom_events,
                DocumentsControllerMixin.custom_events
            ),

            /**
             * @override
             */
            updateButtons() {
                console.log('button kanban');
                this._super(...arguments);
                DocumentsControllerMixin.updateButtons.apply(this, arguments);
                DocumentsApcoControllerMixin.updateButtons.apply(this, arguments);
            },
        }
    );

    return ApcoKanbanController;
});

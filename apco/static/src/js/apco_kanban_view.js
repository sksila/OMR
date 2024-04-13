odoo.define("apco.KanbanView", function (require) {
    "use strict";

    console.log('test apco');

    const ApcoKanbanController = require("apco.KanbanController");
    const KanbanView = require("documents.DocumentsKanbanView");
    const viewRegistry = require("web.view_registry");

    const ApcoKanbanView = KanbanView.extend({
        config: Object.assign({}, KanbanView.prototype.config, {
            Controller: ApcoKanbanController,
        }),
    });

    viewRegistry.add("documents_kanban", ApcoKanbanView);
    return ApcoKanbanView;
});

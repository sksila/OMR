odoo.define("apco.ListView", function (require) {
    "use strict";

    const SpreadsheetListController = require("apco.DocumentsListController");
    const ListView = require("documents.DocumentsListView");
    const viewRegistry = require("web.view_registry");

    const DocumentsListView = ListView.extend({
        config: Object.assign({}, ListView.prototype.config, {
            Controller: SpreadsheetListController,
        }),
    });

    viewRegistry.add("documents_list", DocumentsListView);
    return DocumentsListView;
});

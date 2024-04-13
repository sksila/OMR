odoo.define('spec_utils.kanban', function (require) {
    "use strict";
    var KanbanRenderer = require('web.KanbanRenderer');

    KanbanRenderer.include({

        _setState: function (state) {
            var self = this;
            this._super(state);
            if (this.arch.attrs.sortable) {
                this.columnOptions = _.extend(self.columnOptions, {
                    sortable: this.arch.attrs.sortable === 'true',
                });
            }

            if (this.arch.attrs.drag_and_drop) {
                if (this.arch.attrs.drag_and_drop == 'true') {
                    this.columnOptions.draggable = false;
                }
            }
        },

        _renderGrouped: function (fragment) {
            this._super.apply(this, arguments);
            if (this.columnOptions.sortable === false) {
                // remove previous sorting
                this.$el.sortable('destroy');
            }
        },

    });
});
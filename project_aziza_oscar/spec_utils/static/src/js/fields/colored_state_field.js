odoo.define('spec_utils.colored_state_field', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var registry = require('web.field_registry');
    var core = require('web.core');
    var _t = core._t;
    var ColoredState = AbstractField.extend({
        className: 'colored_state',
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
        },
        /**
         * Display widget
         * @override
         * @private
         */
        _renderReadonly: function () {

            if (this.value) {
                let output = null;

                if (this.attrs.options[this.value]) {
                    let option = this.attrs.options[this.value];
                    output = '<h3><i class="badge badge-pill ' + (option['class'] ? option['class'] : '') + '">' + (option['name'] ? option['name'] : this.value) + '</i></h3>';
                } else {
                    output = this.value;
                }

                this.$el.html(output);
            }
        }
    });

    registry.add('colored_state', ColoredState);
    return ColoredState
});

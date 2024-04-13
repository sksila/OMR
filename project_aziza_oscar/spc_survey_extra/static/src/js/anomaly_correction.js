odoo.define("spc_survey_extra.anomaly_correction", function (require) {
'use strict';

/**
 * This widget is used to hide rows that contains 'hide_row' id in one of its tds
 */

var websiteRootData = require('website.WebsiteRoot');
var Widget = require('web.Widget');

var AnomalyCorrection = Widget.extend({

    // events
    events: {
    },

    custom_events: {
        'loading' : 'd_none_rows'
    },

    init: function () {
        return this._super.apply(this, arguments);
    },

    d_none_rows: function () {
        $('tr[class="d-none"] td').each(function (){
            var current_td = $(this);
            if (current_td.find('[readonly="readonly"][tabindex="-1"]').length == 0) {
                var concerned_column = current_td.find('[data_col_name]').attr('data_col_name');
                current_td.find('input[data_col_name="' + concerned_column + '"]').css('display','none');
                current_td.find('div[data_date_col_name="' + concerned_column + '"]').css('display','none');
                current_td.find('textarea[data_col_name="' + concerned_column + '"]').css('display','none');
                current_td.find('select[data_col_name="' + concerned_column + '"]').css('display','none');
            }
        });
    },

    start: function() {
        var self = this;
        if (location.href.includes("/correction")) {
            $('table tbody tr').each(
                function (index) {
                    var row = $(this);
                    if (row.find('[data_correction="hide_row"]').length != 0 && row.find('[data_correction="show_row"]').length == 0 ) {
                        row.addClass('d-none');
                    }
                }
            )

            setTimeout(function () {
                self.trigger_up('loading')
            },1000);
        }
    },




    });

websiteRootData.websiteRootRegistry.add(AnomalyCorrection, '.js_surveyform');

return AnomalyCorrection;

});


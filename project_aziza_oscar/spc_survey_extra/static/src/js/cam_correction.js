odoo.define("spc_survey_extra.cam_correction", function (require) {
'use strict';

/**
 * This widget is used to hide rows that contains 'hide_row' id in one of its tds
 */

var websiteRootData = require('website.WebsiteRoot');
var Widget = require('web.Widget');

var CamCorrection = Widget.extend({

    // events
    events: {
    },

    init: function () {
        return this._super.apply(this, arguments);
    },

    start: function() {
        if (location.href.includes("/correction")) {
            $('table tbody tr td').each(
                function (index) {
                    var col = $(this);
                    if (col.find("#snapshot").length != 0){
                        // console.log(col);
                        // let hh = col.find('input[type=hidden]');
                        // let hh_value = hh.val();
                        // console.log(hh_value);
                        // console.log(ii_value);
                        // if ((col.find("#snapshot").children().length != 0)) {
                        //     console.log(100);
                        // }
                    }
                    // if (col.find("img").length == 0) {
                    //     col.addClass('d-none');
                    // }
                }
            );
        }
    },


    });

websiteRootData.websiteRootRegistry.add(CamCorrection, '.js_surveyform');

return CamCorrection;

});


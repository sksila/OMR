odoo.define("spc_survey_extra.add_line", function (require) {
'use strict';



var websiteRootData = require('website.WebsiteRoot');
var Widget = require('web.Widget');
var the_form = $('.js_surveyform');


var Addline = Widget.extend({

    events: {
        'click #add_row': 'addRow',
        'click #remove_row': 'removeRow'
    },

    init: function () {
        return this._super.apply(this, arguments);
    },

    addRow: function(e) {
        var table = $('table[name="' + $(e.target).attr('data_table_name') + '"]');
        var tr = table.find("tbody:last-child").append("<tr></tr>"); //append tr to tbdody tag of current table
        //get cols names
        var col_names = [];
        table.find('thead span').each (function() {
            col_names.push($(this).text());
        });
        tr.find('tr:last-child').append('<td><input type="button" value="remove" id="remove_row" /></td>'); //add remove button
        for (var col = 0; col < col_names.length; col++) {
            var rowCnt = table.find("tbody").children().length - 1; //count(tr)
            var field = table.find('tbody tr:first td:eq(' + col + ')').html(); // for copying it to new row
            var reg = /(\d+_\d+_\d+_\d+_\d+)/g;
            var result = field.replace(reg, function(match) {
                var new_row = (parseInt(match.split('_')[3]) + rowCnt).toString(); //increase row
                var replacement = match.split('_')[0] + '_' + match.split('_')[1] + '_' + match.split('_')[2] + '_' + new_row + '_' + match.split('_')[4];
                return replacement;
            });
            var td = tr.find('tr:last-child').append("<td>" + result +"</td>");

        }


    },

    removeRow: function (e) {
        $(e.target).closest('tr').remove();
    }

});

websiteRootData.websiteRootRegistry.add(Addline, '.js_surveyform');

return Addline;

});

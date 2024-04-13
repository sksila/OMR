odoo.define("spc_survey_extra.question_detail_relation", function (require) {
'use strict';



var websiteRootData = require('website.WebsiteRoot');
var Widget = require('web.Widget');
var Addline = require('spc_survey_extra.add_line');

var the_form = $('.js_surveyform');


var QuestionDetailRelation= Widget.extend({

    // events
    events: {
        'change [column]': 'update_details',
        // 'focusout [column]' : 'update_details',
    },

    init: function () {
        return this._super.apply(this, arguments);
    },

    start: function() {
    },


    addLines: function(table_detail,detail_nb_lines) {

        //cleaning
        var tbody = table_detail.find("tbody");
        if(!tbody.is(':visible')) {
            tbody.show();
            tbody.find("input[name$='_details']").css('display','');
            tbody.find("div[name$='_details']").css('display','');
            tbody.find("textarea[name$='_details']").css('display','');
            tbody.find("select[name$='_details']").css('display','');
        }
        if (tbody.find('tr').length > 1) {
            tbody.find('tr:not(:first)').remove();
        }
        // end cleaning

        var tr = table_detail.find("tbody:last-child").append("<tr></tr>"); //append tr to tbdody tag of current table
        // //get cols names
        var col_names = [];
        table_detail.find('thead span').each (function() {
            col_names.push($(this).text());
        });


        if (detail_nb_lines == 0) {
            tbody.hide();
            tbody.find("input[name$='_details']").css('display','none');
            tbody.find("div[name$='_details']").css('display','none');
            tbody.find("textarea[name$='_details']").css('display','none');
            tbody.find("select[name$='_details']").css('display','none');
        }

        for (var count=0; count < detail_nb_lines-1; count++){ //compter a partir de 1 (prendre en consideration le row existant)
            tr.find('tr:last-child').append('<td></td>');
            for (var col = 0; col < col_names.length; col++) {
                var rowCnt = table_detail.find("tbody").children().length - 1; //count(tr)
                var field = table_detail.find('tbody tr:first td:eq(' + col + ')').html(); // for copying it to new row
                var reg = /(\d+_\d+_\d+_\d+_\d+)/g;
                var result = field.replace(reg, function(match) {
                    var new_row = (parseInt(match.split('_')[3]) + rowCnt).toString(); //increase row
                    var replacement = match.split('_')[0] + '_' + match.split('_')[1] + '_' + match.split('_')[2] + '_' + new_row + '_' + match.split('_')[4];
                    return replacement;
                });
                var td = tr.find('tr:last-child').append("<td>" + result +"</td>");

            }
            var tr = table_detail.find("tbody:last-child").append("<tr></tr>");
        }


    },

    update_details: function(e) {
        if ($(e.target).closest('table').find("input[name*='question_detail_relation']").length) { //question_detail_relation
            var current_formula = []
            var formula = JSON.parse($(e.target).closest('table').find("input[name*='question_detail_relation']").val());
            var current_row = $(e.target).closest('tr');
            var current_line = current_row.find('th span').text(); // row question
            for(let item in formula ){ //get only row formulas
                if (formula[item]['row'] == current_line) {
                    current_formula.push(formula[item]);
                }
            }
            for (let item in current_formula){ //loop row formulas one by one
                    var condition = current_formula[item]['condition'];
                    //get cols names
                    var col_names = [];
                    current_row.find('td').each (function() {
                        col_names.push($(this).find('[data_col_name]').attr('data_col_name'));
                    });
                    //update condition
                    var col;
                    for (col=0; col<col_names.length; col++) {
                        if(condition.includes(col_names[col])) {
                            condition = condition.split(col_names[col]).join("current_row.find('[data_col_name = \"" + col_names[col] + "\"]').val()"); //replaceALL
                        }
                    }
                    /*eval condition*/
                    var is_condition_true = eval(condition);
                    if (is_condition_true) {
                        if (current_formula[item]['details_nb_lines']) { // != false
                            var result = current_formula[item]['details_nb_lines'];
                            //check if result is an operation :
                            var result_formula_test = /^\(.*\)$/; //start with ( and end with )
                            if (result.match(result_formula_test)) {
                                //update result
                                var col;
                                for (col = 0; col < col_names.length; col++) {
                                    if (result.includes(col_names[col])) {
                                        var col_value = current_row.find('[data_col_name = ' + col_names[col] + ']').val();
                                        result = result.split(col_names[col]).join(col_value); //replaceALL
                                    }
                                }
                                var result = eval(result);
                            }
                            var table_detail_name = $(e.target).closest('table').attr('name') + '_details';
                            var table_detail = $('table[name="' + table_detail_name + '"]');
                            this.addLines(table_detail,result);
                        }
                        else {
                            console.log('result is wrong');
                        }
                    }
                    else {
                        console.log('condition is wrong!');
                    }
            }

        }


    }


    });

websiteRootData.websiteRootRegistry.add(QuestionDetailRelation, '.js_surveyform');

return QuestionDetailRelation;

});


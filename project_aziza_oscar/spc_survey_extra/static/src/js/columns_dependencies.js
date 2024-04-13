odoo.define("spc_survey_extra.anomaly_correction", function (require) {
'use strict';



var websiteRootData = require('website.WebsiteRoot');
var Widget = require('web.Widget');
var the_form = $('.js_surveyform');


var ColumnsDependencies = Widget.extend({

    // events
    events: {
        'change [column]': 'update',
        // 'click [column]': 'update',
        // 'focusin [column]' : 'update',
        'focusout [column]' : 'update',

    },

    init: function () {
        return this._super.apply(this, arguments);
    },

    start: function() {
        $('[data-col_dependency_style="readonly_columns"]').each(
                function (index) {
                    if ($(this).is("select")) {
                        $(this).css('pointer-events','none');
                        $(this).attr('readonly','readonly');
                        $(this).attr('tabindex','-1');
                    }
                    else {
                        $(this).attr('readonly','readonly');
                        $(this).attr('tabindex','-1');
                    }
                })
    },

    update: function(e) {
        //columns :
        if ($(e.target).closest('table').find("input[name*='columns_dependencies']").length) {
            var formula = JSON.parse($(e.target).closest('table').find("input[name*='columns_dependencies']").val());
            var current_row = $(e.target).closest('tr');
            current_row.find('td').each (function(index,td) {
                var current_td = $(this);
                var current_formula = [];
                if (current_td.find('[style="display:none;"]').length == 0) {
                    for(let item in formula){ //get only column formulas
                        if (formula[item]['column'] == current_td.find('[data_col_name]').attr('data_col_name')) {
                            current_formula.push(formula[item]);
                        }
                    }
                    if (current_formula.length != 0) {
                        //get cols names
                        var col_names = [];
                        current_row.find('td').each (function() {
                            col_names.push($(this).find('[data_col_name]').attr('data_col_name'));
                        });
                        if (current_formula.length == 1) {
                            var condition = current_formula[0]['condition'];
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
                                if (current_formula[0]['result']) {
                                    var result = current_formula[0]['result'];
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
                                        var result_evaluation = eval(result);
                                        //eval result
                                        if (result_evaluation) {
                                            current_td.find('[column]').val(result_evaluation);
                                        }
                                        if (result_evaluation == 0) {
                                            current_td.find('[column]').val(0);
                                        }
                                    }
                                }
                                else { //else: result is not an operation
                                    current_td.find('[column]').val(result);
                                }


                            }
                            else {
                                if (current_formula[0]['reverse_result']) { // != false

                                    var reverse_result = current_formula[0]['reverse_result'];
                                    //check if reverse_result is an operation :
                                    var reverse_result_formula_test = /^\(.*\)$/; //start with ( and end with )
                                    if (reverse_result.match(reverse_result_formula_test)){
                                        //update reverse_result
                                        var col;
                                        for (col=0; col<col_names.length; col++) {
                                            if(reverse_result.includes(col_names[col])) {
                                                var col_value = current_row.find('[data_col_name = ' + col_names[col] + ']').val();
                                                reverse_result = reverse_result.split(col_names[col]).join(col_value); //replaceALL
                                            }
                                        }
                                        var reverse_result_evaluation = eval(reverse_result);
                                        //eval reverse_result
                                        if (reverse_result_evaluation) {
                                            current_td.find('[column]').val(reverse_result_evaluation);
                                        }
                                        if (reverse_result_evaluation == 0) {
                                            current_td.find('[column]').val(0);
                                        }
                                    }
                                }
                                else {
                                    current_td.find('[column]').val('');
                                }
                            }

                        }
                        else {
                            var done = 0;
                            for(let formula in current_formula){
                                if (current_formula[formula]['column'] == current_td.find('[data_col_name]').attr('data_col_name')) {
                                    var condition = current_formula[formula]['condition'];
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
                                        if (current_formula[formula]['result']) {
                                            var result = current_formula[formula]['result'];
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
                                                var result_evaluation = eval(result);
                                                //eval result
                                                if (result_evaluation) {
                                                    current_td.find('[column]').val(result_evaluation);
                                                }
                                                if (result_evaluation == 0) {
                                                    current_td.find('[column]').val(0);
                                                }
                                            }
                                        }
                                        done = 1
                                    }
                                }
                                if (done == 1) {
                                    break;
                                }
                            }
                            if (done == 0) {
                                if (current_formula[current_formula.length - 1]['reverse_result']) {
                                   var reverse_result = current_formula[current_formula.length - 1]['reverse_result'];
                                    //check if reverse_result is an operation :
                                    var reverse_result_formula_test = /^\(.*\)$/; //start with ( and end with )
                                    if (reverse_result.match(reverse_result_formula_test)){
                                        //update reverse_result
                                        var col;
                                        for (col=0; col<col_names.length; col++) {
                                            if(reverse_result.includes(col_names[col])) {
                                                var col_value = current_row.find('[data_col_name = ' + col_names[col] + ']').val();
                                                reverse_result = reverse_result.split(col_names[col]).join(col_value); //replaceALL
                                            }
                                        }
                                        var reverse_result_evaluation = eval(reverse_result);
                                        //eval reverse_result
                                        if (reverse_result_evaluation) {
                                            current_td.find('[column]').val(reverse_result_evaluation);
                                        }
                                        if (reverse_result_evaluation == 0) {
                                            current_td.find('[column]').val(0);
                                        }
                                    }
                                }
                                else {
                                   current_td.find('[column]').val('');
                                }
                            }
                        }
                    }
                }
            });

        }


        if ($(e.target).closest('table').find("input[name*='rows_columns_dependencies']").length) { //row_columns dependencies
            var current_formula = []
            var formula = JSON.parse($(e.target).closest('table').find("input[name*='rows_columns_dependencies']").val());
            var current_row = $(e.target).closest('tr');
            var current_line = current_row.find('th span').text(); // row question
            for(let item in formula ){ //get only row formulas
                if (formula[item]['row'] == current_line) {
                    current_formula.push(formula[item])
                }
            }
            for (let item in current_formula){ //loop row formulas one by one
                current_row.find('td').each (function(index,td) { //loop tds inside current tr
                var current_td = $(this);
                if (current_td.find('[style="display:none;"]').length == 0 && current_formula[item]['column'] == current_td.find('[data_col_name]').attr('data_col_name')) { //check if current column has condition
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
                        if (current_formula[item]['result']) { // != false
                            var result = current_formula[item]['result'];
                            //check if result is an operation :
                            var result_formula_test = /^\(.*\)$/; //start with ( and end with )

                            if (result.match(result_formula_test)){
                                    //update result
                                    var col;
                                    for (col=0; col<col_names.length; col++) {
                                        if(result.includes(col_names[col])) {
                                            var col_value = current_row.find('[data_col_name = ' + col_names[col] + ']').val();
                                            result = result.split(col_names[col]).join(col_value); //replaceALL
                                        }
                                    }
                                    var result_evaluation = eval(result);
                                    //eval result
                                    if (result_evaluation) {
                                        current_td.find('[column]').val(result_evaluation);
                                    }
                                    if (result_evaluation == 0) {
                                        current_td.find('[column]').val(0);
                                    }
                                }
                        }
                        else {
                            current_td.find('[column]').val('');
                        }
                    }
                    else {
                        if (current_formula[item]['reverse_result']) { // != false
                            var reverse_result = current_formula[item]['reverse_result'];
                            //check if reverse_result is an operation :
                            var reverse_result_formula_test = /^\(.*\)$/; //start with ( and end with )
                            if (reverse_result.match(reverse_result_formula_test)){
                                    //update reverse_result
                                    var col;
                                    for (col=0; col<col_names.length; col++) {
                                        if(reverse_result.includes(col_names[col])) {
                                            var col_value = current_row.find('[data_col_name = ' + col_names[col] + ']').val();
                                            reverse_result = reverse_result.split(col_names[col]).join(col_value); //replaceALL
                                        }
                                    }
                                    var reverse_result_evaluation = eval(reverse_result);
                                    //eval reverse_result
                                    if (reverse_result_evaluation) {
                                        current_td.find('[column]').val(reverse_result_evaluation);
                                    }
                                    if (reverse_result_evaluation == 0) {
                                        current_td.find('[column]').val(0);
                                    }
                                }
                        }
                        else {
                            current_td.find('[column]').val('');
                        }
                    }
                }
                });
            }

        }


    }


    });

websiteRootData.websiteRootRegistry.add(ColumnsDependencies, '.js_surveyform');

return ColumnsDependencies;

});


odoo.define("spc_survey_extra.show_hide_cond", function (require) {
'use strict';



var websiteRootData = require('website.WebsiteRoot');
var Widget = require('web.Widget');
var the_form = $('.js_surveyform');


var ShowHideCond = Widget.extend({

    // events
    events: {
        'change [column]': 'update',
    },

    custom_events: {
        'loading' : 'starting'
    },

    init: function () {
        return this._super.apply(this, arguments);
    },

    start: function() {
        var self = this;
        if (location.href.includes("/correction")) {
            setTimeout(function () {
                self.trigger_up('loading')
            },1000);
        }
    },

    starting: function () {
        var list = $('.js_surveyform').find("input[name*='show_hide_cond_ids']");
        list.each(function() { //parcourir question par question
           var table = $(this).closest('table').attr('name');
           var col_names = [];
           $(this).closest('table').find('tbody tr:eq(0)').find('td').each (function() { //get cols names
               col_names.push($(this).find('[data_col_name]').attr('data_col_name'));
           });
           var formula = JSON.parse($(this).closest('table').find("input[name*='show_hide_cond_ids']").val());
           var lines = $(this).closest('table').find('tbody tr th span');
           lines.each(function(index) {
               var current_formula = [];
               for(let item in formula){
                   if (formula[item]['row'] == $(this).text() ||  formula[item]['concerned_rows'].includes($(this).text())) {
                       current_formula.push(formula[item]);
                   }
               }
               current_formula.map((item,idx) => current_formula[current_formula.length-1-idx]);
               for (let item in current_formula){ //loop row formulas one by one
                    if (current_formula[item]['type'] == 'same_line') {
                        var current_row = $(this).closest('tr');
                        current_row.find('td').each (function(index,td) { //loop tds inside current tr
                            var current_td = $(this);
                            if (current_td.find('[style="display:none;"]').length == 0 && current_formula[item]['column'] == current_td.find('[data_col_name]').attr('data_col_name')) { //check if current column has condition
                                var concerned_column = current_formula[item]['column'];
                                var condition = current_formula[item]['condition'];
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
                                        current_row.find('input[data_col_name="' + concerned_column + '"]').css('display','none');
                                        current_row.find('input[data_col_name="' + concerned_column + '"]').val('');
                                        current_row.find('div[data_date_col_name="' + concerned_column + '"]').css('display','none');
                                        current_row.find('textarea[data_col_name="' + concerned_column + '"]').css('display','none');
                                        current_row.find('select[data_col_name="' + concerned_column + '"]').css('display','none');
                                        current_row.find('select[data_col_name="' + concerned_column + '"]').prop('selectedIndex', 0);
                                }
                                else {
                                        current_row.find('input[data_col_name="' + concerned_column + '"]').css('display','');
                                        current_row.find('div[data_date_col_name="' + concerned_column + '"]').css('display','');
                                        current_row.find('textarea[data_col_name="' + concerned_column + '"]').css('display','');
                                        current_row.find('select[data_col_name="' + concerned_column + '"]').css('display','');
                                }
                            }
                        });
                    }
                    if (current_formula[item]['type'] == 'different_line') {
                        var condition = current_formula[item]['condition'];
                        var concerned_rows = current_formula[item]['concerned_rows'];
                        var row;
                        for (row=0; row<concerned_rows.length;row++){ //update rows
                            if(condition.includes(concerned_rows[row])) {
                                condition = condition.split(concerned_rows[row]).join("$('table[name=\"" + table + "\"] span:contains(\"" + concerned_rows[row]+ "\")').closest('tr')"); //replaceALL
                            }
                        }
                        //update condition
                        var col;
                        for (col=0; col<col_names.length; col++) {
                            if(condition.includes(col_names[col])) {
                                condition = condition.split(col_names[col]).join("find('[data_col_name = \"" + col_names[col] + "\"]').val()"); //replaceALL
                            }
                        }
                        /*eval condition*/
                        var is_condition_true = eval(condition);
                        var line = $('table[name="' + table + '"] span:contains("' + current_formula[item]['row']+ '")').closest('tr');
                        if (is_condition_true) {
                            line.find('input[data_col_name="' + current_formula[item]['column'] + '"]').css('display','none');
                            line.find('input[data_col_name="' + current_formula[item]['column'] + '"]').val('');
                            line.find('div[data_date_col_name="' + current_formula[item]['column'] + '"]').css('display','none');
                            line.find('textarea[data_col_name="' + current_formula[item]['column'] + '"]').css('display','none');
                            line.find('select[data_col_name="' + current_formula[item]['column'] + '"]').css('display','none');
                            line.find('select[data_col_name="' + current_formula[item]['column'] + '"]').prop('selectedIndex', 0);
                        }
                        else {
                            line.find('input[data_col_name="' + current_formula[item]['column'] + '"]').css('display','');
                            line.find('div[data_date_col_name="' + current_formula[item]['column'] + '"]').css('display','');
                            line.find('textarea[data_col_name="' + current_formula[item]['column'] + '"]').css('display','');
                            line.find('select[data_col_name="' + current_formula[item]['column'] + '"]').css('display','');
                        }

                    }
               }
               var current_formula = [];
           });

        });
    },

    update: function(e) {
        if ($(e.target).closest('table').find("input[name*='show_hide_cond_ids']").length) { //show_hide_cond_ids
            var current_formula = []
            var concerned_columns = []
            var formula = JSON.parse($(e.target).closest('table').find("input[name*='show_hide_cond_ids']").val());
            var current_row = $(e.target).closest('tr');
            var current_line = current_row.find('th span').text(); // row question
            for(let item in formula ){ //get only row formulas
                if (formula[item]['row'] == current_line ||  formula[item]['concerned_rows'].includes(current_line)) {
                    current_formula.push(formula[item]);
                }
            }
            current_formula.map((item,idx) => current_formula[current_formula.length-1-idx])
            // current_formula.reverse();
            for (let item in current_formula){ //loop row formulas one by one
                if (current_formula[item]['type'] == 'same_line') {

                    current_row.find('td').each (function(index,td) { //loop tds inside current tr
                        var current_td = $(this);
                        if (current_td.find('[style="display:none;"]').length == 0 && current_formula[item]['column'] == current_td.find('[data_col_name]').attr('data_col_name')) { //check if current column has condition
                            var concerned_column = current_formula[item]['column'];
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
                                    current_row.find('input[data_col_name="' + concerned_column + '"]').css('display','none');
                                    current_row.find('input[data_col_name="' + concerned_column + '"]').val('');
                                    current_row.find('div[data_date_col_name="' + concerned_column + '"]').css('display','none');
                                    current_row.find('textarea[data_col_name="' + concerned_column + '"]').css('display','none');
                                    current_row.find('select[data_col_name="' + concerned_column + '"]').css('display','none');
                                    current_row.find('select[data_col_name="' + concerned_column + '"]').prop('selectedIndex', 0);
                            }
                            else {
                                    current_row.find('input[data_col_name="' + concerned_column + '"]').css('display','');
                                    current_row.find('div[data_date_col_name="' + concerned_column + '"]').css('display','');
                                    current_row.find('textarea[data_col_name="' + concerned_column + '"]').css('display','');
                                    current_row.find('select[data_col_name="' + concerned_column + '"]').css('display','');
                            }
                        }
                    });

                }
                if (current_formula[item]['type'] == 'different_line') {
                    var table = $(e.target).closest('table').attr('name');
                    var condition = current_formula[item]['condition'];
                    var concerned_rows = current_formula[item]['concerned_rows'];
                    //get cols names
                    var col_names = [];
                    current_row.find('td').each (function() {
                        col_names.push($(this).find('[data_col_name]').attr('data_col_name'));
                    });
                    //update rows
                    var row;
                    for (row=0; row<concerned_rows.length;row++){
                        if(condition.includes(concerned_rows[row])) {
                            condition = condition.split(concerned_rows[row]).join("$('table[name=\"" + table + "\"] span:contains(\"" + concerned_rows[row]+ "\")').closest('tr')"); //replaceALL
                        }
                    }
                    //update condition
                    var col;
                    for (col=0; col<col_names.length; col++) {
                        if(condition.includes(col_names[col])) {
                            condition = condition.split(col_names[col]).join("find('[data_col_name = \"" + col_names[col] + "\"]').val()"); //replaceALL
                        }
                    }
                    /*eval condition*/
                    var is_condition_true = eval(condition);
                    var line = $('table[name="' + table + '"] span:contains("' + current_formula[item]['row']+ '")').closest('tr');
                    if (is_condition_true) {
                        line.find('input[data_col_name="' + current_formula[item]['column'] + '"]').css('display','none');
                        line.find('input[data_col_name="' + current_formula[item]['column'] + '"]').val('');
                        line.find('div[data_date_col_name="' + current_formula[item]['column'] + '"]').css('display','none');
                        line.find('textarea[data_col_name="' + current_formula[item]['column'] + '"]').css('display','none');
                        line.find('select[data_col_name="' + current_formula[item]['column'] + '"]').css('display','none');
                        line.find('select[data_col_name="' + current_formula[item]['column'] + '"]').prop('selectedIndex', 0);
                    }
                    else {
                        line.find('input[data_col_name="' + current_formula[item]['column'] + '"]').css('display','');
                        line.find('div[data_date_col_name="' + current_formula[item]['column'] + '"]').css('display','');
                        line.find('textarea[data_col_name="' + current_formula[item]['column'] + '"]').css('display','');
                        line.find('select[data_col_name="' + current_formula[item]['column'] + '"]').css('display','');
                    }


                }

            }

        }


    }


    });

websiteRootData.websiteRootRegistry.add(ShowHideCond, '.js_surveyform');

return ShowHideCond;

});


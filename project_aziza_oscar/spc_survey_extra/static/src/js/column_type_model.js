odoo.define("spc_survey_extra.column_type_model", function (require) {
'use strict';

/**
 * This widget render the model column type available list
 */

var websiteRootData = require('website.WebsiteRoot');
var Widget = require('web.Widget');

var ColumnTypeModel = Widget.extend({

    // events
    events: {
        'click .column_type_model': '_onclick_column_type_model',
        'focusin .column_type_model': '_onclick_column_type_model',
        'change .column_type_model': '_focusout_column_type_model',
    },

    init: function () {
        return this._super.apply(this, arguments);
    },


    _onclick_column_type_model : function (ev) {
        var table = $(ev.target).closest('table');
        var availableList = [];
        var model = $(ev.target).data('model');
        var token = $('.js_surveyform').find("input[name='token']").val();
        var question = $(ev.target).closest("div[class='js_question-wrapper']").attr('id');
        var column = $(ev.target).attr('data_col_name');
        var filter_field = $(ev.target).attr('data_filter_field');
        var is_filter_on = $(ev.target).attr('data_is_filter_on');
        var filter_value = "undefined";
        /*
        * if is_filter_on get the filter input content: if it is filled send it to function else show an error msg
        * */
        if (is_filter_on == '1') {
            var filter_value = $(ev.target).parent().find('input.closest_filter').val();
        }
        var self = this;
        self._rpc({
                model: 'column_type_model.rpc' ,
                method: 'get_model_records',
                args: [String(model),String(token),String(question),String(column),String(filter_field),String(is_filter_on),String(filter_value)],
            }).then(function (result) {
                    for (let list of result) {
                        availableList.push(list)
                    }
                    var arrayOfValues = [];
                    table.find('input.column_type_model[data_is_filter_on]').each(function(){ //[data_is_filter_on] afin d'éviter l'input du filtre
                        var value = $(this).val();
                        if (value) {
                            arrayOfValues.push(value);
                        }
                    });
                    for(var i in arrayOfValues){
                        if(availableList.indexOf(arrayOfValues[i]) !== -1){
                            const index = availableList.indexOf(arrayOfValues[i]);
                            if (index > -1) { availableList.splice(index, 1) }
                        }
                    }

                    arrayOfValues = []

            });

        $(ev.target).autocomplete({
	          source: availableList,
              minLength: 3
//	          source: availableTags
	        });

        },

        _focusout_column_type_model : function (ev) {
            var input_value = $(ev.target).val();
            var model = $(ev.target).data('model');
            var filter_field = $(ev.target).attr('data_filter_field');
            var is_filter_on = $(ev.target).attr('data_is_filter_on');
            var self = this;
            self._rpc({
                    model: 'column_type_model.rpc' ,
                    method: 'check_in_model_recorde',
                    args: [String(model),String(input_value),String(filter_field),String(is_filter_on)],
                }).then(function (result) {
                    if (result === 0) {
                        alert($(ev.target).val() + ' is not in list. \n Choose value from list!');
                        $(ev.target).val('');
                    }

            })
        },

    });

websiteRootData.websiteRootRegistry.add(ColumnTypeModel, '.js_surveyform');

return ColumnTypeModel;

});


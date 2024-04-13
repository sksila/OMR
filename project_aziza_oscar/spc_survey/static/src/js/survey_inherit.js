odoo.define('survey.survey', function (require) {
'use strict';

require('web.dom_ready');
var core = require('web.core');
var time = require('web.time');
var ajax = require('web.ajax');
var base = require('web_editor.base');
var context = require('web_editor.context');
var field_utils = require('web.field_utils');

var _t = core._t;
/*
 * This file is intended to add interactivity to survey forms
 */

var the_form = $('.js_surveyform');

if(!the_form.length) {
    $('.loading_class').on('click', function() {
        $(this).html("<i class='fa fa-spinner fa-spin'></i> Loading");
    });
    return $.Deferred().reject("DOM doesn't contain '.js_surveyform'");
}

    console.debug("[survey] Custom JS for survey is loading...");

    var prefill_controller = the_form.attr("data-prefill");
    var submit_controller = the_form.attr("data-submit");
    var scores_controller = the_form.attr("data-scores");
    var print_mode = false;
    var quiz_correction_mode = false;
    let the_case = $( "input[name='case']" ).val();
    let save_controller = the_form.attr("data-save");

    // Printing mode: will disable all the controls in the form
    if (_.isUndefined(submit_controller) && the_case != 'edit' ) {
        $(".js_surveyform .input-group-text span.fa-calendar").css("pointer-events", "none");
        $('.js_surveyform :input').prop('disabled', true);
        print_mode = true;
    }

    // Quiz correction mode
    if (! _.isUndefined(scores_controller)) {
        quiz_correction_mode = true;
    }


    // Custom code for right behavior of radio buttons with comments box
    $('.js_comments>input[type="text"]').focusin(function(){
        $(this).prev().find('>input').attr("checked","checked");
    });
    $('.js_radio input[type="radio"][data-oe-survey-otherr!="1"]').click(function(){
        $(this).closest('.js_radio').find('.js_comments>input[type="text"]').val("");
    });
    $('.js_comments input[type="radio"]').click(function(){
        $(this).closest('.js_comments').find('>input[data-oe-survey-othert="1"]').focus();
    });
    // Custom code for right behavior of dropdown menu with comments
    $('.js_drop input[data-oe-survey-othert="1"]').hide();
    $('.js_drop select').change(function(){
        var other_val = $(this).find('.js_other_option').val();
        if($(this).val() === other_val){
            $(this).parent().removeClass('col-lg-12').addClass('col-lg-6');
            $(this).closest('.js_drop').find('input[data-oe-survey-othert="1"]').show().focus();
        }
        else{
            $(this).parent().removeClass('col-lg-6').addClass('col-lg-12');
            $(this).closest('.js_drop').find('input[data-oe-survey-othert="1"]').val("").hide();
        }
    });
    // Custom code for right behavior of checkboxes with comments box
    $('.js_ck_comments>input[type="text"]').focusin(function(){
        $(this).prev().find('>input').attr("checked","checked");
    });
    $('.js_ck_comments input[type="checkbox"]').change(function(){
        if (! $(this).prop("checked")){
            $(this).closest('.js_ck_comments').find('input[type="text"]').val("");
        }
    });

    // Pre-filling of the form with previous answers
    function prefill(){
        if (! _.isUndefined(prefill_controller)) {
            var prefill_def = $.ajax(prefill_controller, {dataType: "json"})
                .done(function(json_data){
                    _.each(json_data, function(value, key){
                        // prefill of text/number/date boxes
                        var input = the_form.find(".form-control[name=" + key + "]");
                        if (input.attr('date')) {
                            // display dates in user timezone
                            var moment_date = field_utils.parse.date(value[0]);
                            value = field_utils.format.date(moment_date, null, {timezone: true});
                        }

                        // cam case
                        var snp = the_form.find(".picture-div[name=" + key + "]").find("#snapshot");
                        var cam_button = the_form.find(".picture-div[name=" + key + "]").find(".play");
                        if (snp.length != 0) {
                            let img = new Image();
                            img.src = value;
                            img.height = 200;
                            img.width = 200;
                            snp.append(img);
                            if (the_case != 'edit') //print case
                            {
                                cam_button.addClass('d-none') //hide cam button
                            }

                        }
                        // end cam case

                        //attachment case
                        var attach_ul = the_form.find("ul[name=" + key + "]");
                        if (attach_ul.length != 0) {
                            value[0].forEach(function (item, index) {
                                attach_ul.append('<li> ' +
                                                    '<a target="_blank" href="' +
                                                    item[1] +'">' + item[0] + '</a></li>');
                            });
                            if (the_case != 'edit') //print case
                                {
                                    input.addClass('d-none'); //hide upload button
                                }
                        }
                        //end attachment case

                        if (attach_ul.length == 0) //all cases except attachment case
                        {
                            input.val(value);
                        }

                        // special case for comments under multiple suggestions questions
                        if (_.string.endsWith(key, "_comment") &&
                            (input.parent().hasClass("js_comments") || input.parent().hasClass("js_ck_comments"))) {
                            input.siblings().find('>input').attr("checked","checked");
                        }

                        // checkboxes and radios
                        the_form.find("input[name^='" + key + "_'][type='checkbox']").each(function(){
                            $(this).val(value);
                        });
                        if (attach_ul.length == 0) {
                            the_form.find("input[name=" + key + "][type!='text']").each(function () {
                                $(this).val(value);
                            });
                        }
                    });
                })
                .fail(function(){
                    console.warn("[survey] Unable to load prefill data");
                });
            return prefill_def;
        }
    }

    // Display score if quiz correction mode
    function display_scores(){
        if (! _.isUndefined(scores_controller)) {
            var score_def = $.ajax(scores_controller, {dataType: "json"})
                .done(function(json_data){
                    _.each(json_data, function(value, key){
                        the_form.find("span[data-score-question=" + key + "]").text("Your score: " + value);
                    });
                })
                .fail(function(){
                    console.warn("[survey] Unable to load score data");
                });
            return score_def;
        }
    }

    // Parameters for form submission
    $('.js_surveyform').ajaxForm({
        url: submit_controller,
        type: 'POST',                       // submission type
        dataType: 'json',                   // answer expected type
        beforeSubmit: function(formData, $form, options){           // hide previous errmsg before resubmitting
            var display_none = [];
            for (var i=0; i<formData.length; i++) {
                var input = the_form.find(".form-control[name=" + formData[i]['name'] + "]");
                var style = input.attr('style');
                formData[i]['style'] = style;
                if (typeof style !== 'undefined') {
                    if (style.includes('display:none') || style.includes('display: none')) {
                        display_none.push(formData[i]['name']);
                    }
                }
            }
            formData[formData.length] = { "name": "display_none", "value": display_none };
            var date_fields = $form.find('div.date > input.form-control');
            for (var i=0; i < date_fields.length; i++) {
                var el = date_fields[i];
                var moment_date = el.value !== '' ? field_utils.parse.date(el.value) : '';
                if (moment_date) {
                    moment_date.toJSON = function () {
                        return this.clone().locale('en').format('YYYY-MM-DD');
                    };
                }
                var field_obj = _.findWhere(formData, {'name': el.name});
                field_obj.value = JSON.parse(JSON.stringify(moment_date));
            }
            $('.js_errzone').html("").hide();
        },
        success: function(response, status, xhr, wfe){ // submission attempt
            if(_.has(response, 'errors')){  // some questions have errors
                _.each(_.keys(response.errors), function(key){
                    $("#" + key + '>.js_errzone').append('<p>' + response.errors[key] + '</p>').show();
                    var required_element = $("#" + key + '>.js_errzone').find('span').text();
                    var line = $("[name='" + required_element + "']").closest('tr').find('th span').text();
                    var column = $("[name='" + required_element + "']").attr('data_col_name');
                    $("#" + key + '>.js_errzone').append('<p><mark>' + line + ' / ' + column + '</mark></p>');
                    $("[name='" + required_element + "']").focus();
                });
                return false;
            }
            else if (_.has(response, 'redirect')){      // form is ok
                window.location.replace(response.redirect);
                return true;
            }
            else {                                      // server sends bad data
                console.error("Incorrect answer sent by server");
                return false;
            }
        },
        // timeout: 5000,
        error: function(jqXHR, textStatus, errorThrown){ // failure of AJAX request
            $('#AJAXErrorModal').modal('show');
        }
    });

    //save_controller
    if (the_case == 'edit') {
        $('.js_surveyform').ajaxForm({
            url: save_controller,
            type: 'POST',                       // submission type
            dataType: 'json',                   // answer expected type
            beforeSubmit: function (formData, $form, options) {           // hide previous errmsg before resubmitting
                var display_none = [];
                for (var i=0; i<formData.length; i++) {
                    var input = the_form.find(".form-control[name=" + formData[i]['name'] + "]");
                    var style = input.attr('style');
                    formData[i]['style'] = style;
                    if (typeof style !== 'undefined') {
                        if (style.includes('display:none') || style.includes('display: none')) {
                            display_none.push(formData[i]['name']);
                        }
                    }
                }
                formData[formData.length] = { "name": "display_none", "value": display_none };


                var date_fields = $form.find('div.date > input.form-control');
                for (var i = 0; i < date_fields.length; i++) {
                    var el = date_fields[i];
                    var moment_date = el.value !== '' ? field_utils.parse.date(el.value) : '';
                    if (moment_date) {
                        moment_date.toJSON = function () {
                            return this.clone().locale('en').format('YYYY-MM-DD');
                        };
                    }
                    var field_obj = _.findWhere(formData, {'name': el.name});
                    field_obj.value = JSON.parse(JSON.stringify(moment_date));
                }
                $('.js_errzone').html("").hide();
            },
            success: function (response, status, xhr, wfe) { // submission attempt
                if (_.has(response, 'errors')) {  // some questions have errors
                    _.each(_.keys(response.errors), function (key) {
                        $("#" + key + '>.js_errzone').append('<p>' + response.errors[key] + '</p>').show();
                        var required_element = $("#" + key + '>.js_errzone').find('span').text();
                        var line = $("[name='" + required_element + "']").closest('tr').find('th span').text();
                        var column = $("[name='" + required_element + "']").attr('data_col_name');
                        $("#" + key + '>.js_errzone').append('<p><mark>' + line + ' / ' + column + '</mark></p>');
                        $("[name='" + required_element + "']").focus();
                    });
                    return false;
                } else if (_.has(response, 'redirect')) {      // form is ok
                    window.location.replace(response.redirect);
                    return true;
                } else {                                      // server sends bad data
                    console.error("Incorrect answer sent by server");
                    return false;
                }
            },
            // timeout: 5000,
            error: function (jqXHR, textStatus, errorThrown) { // failure of AJAX request
                $('#AJAXErrorModal').modal('show');
            }
        });
    }


    // // Handles the event when a question is focused out
    // $('.js_question-wrapper').focusout(
    //     function(){
    //         console.debug("[survey] Focus lost on question " + $(this).attr("id"));
    // });

    function load_locale(){
        var url = "/web/webclient/locale/" + context.get().lang || 'en_US';
        return ajax.loadJS(url);
    }

    var ready_with_locale = $.when(base.ready(), load_locale());
    // datetimepicker use moment locale to display date format according to language
    // frontend does not load moment locale at all.
    // so wait until DOM ready with locale then init datetimepicker
    ready_with_locale.then(function(){
         _.each($('.input-group.date'), function(date_field){
            var minDate = $(date_field).data('mindate') || moment({ y: 1900 });
            var maxDate = $(date_field).data('maxdate') || moment().add(200, "y");
            $('#' + date_field.id).datetimepicker({
                format : time.getLangDateFormat(),
                minDate: minDate,
                maxDate: maxDate,
                calendarWeeks: true,
                icons: {
                    time: 'fa fa-clock-o',
                    date: 'fa fa-calendar',
                    next: 'fa fa-chevron-right',
                    previous: 'fa fa-chevron-left',
                    up: 'fa fa-chevron-up',
                    down: 'fa fa-chevron-down',
                },
                locale : moment.locale(),
                allowInputToggle: true,
                keyBinds: null,
                //Bypass that minDate is a default value of datetimepicker input
                useCurrent: false
            });

        });
        // Launch prefilling
        prefill();
        if(quiz_correction_mode === true){
            display_scores();
        }
    });

    console.debug("[survey] Custom JS for survey loaded!");

    $('.loading_class').on('click', function() {
        $(this).html("<i class='fa fa-spinner fa-spin'></i> Loading");
    });

    // // automatic resize of all the input type text and number
    function resizeInput() {
        $(this).attr('size', ($(this).val().length) * 1.1);
        $(this).addClass("w-auto");
    }

    function resizeInputNumber() {
        $(this).attr('size', ($(this).val().length) * 1.1);
        $(this).addClass("w-auto");
    }

    function resizeTextarea() {
        $(this).addClass("w-auto");
    }

    $('input[type="text"]').keyup(resizeInput).each(resizeInput); //field_model_col
    $('input[type="text"]').change(resizeInput).each(resizeInput);
    $('input[type="search"]').keyup(resizeInput).each(resizeInput);
    $('input[type="search"]').change(resizeInput).each(resizeInput);
    // $('input[type="search"]').each(function () {
    //     $(this).attr('size', 54);
    // });
    $('input[type="number"]').keyup(resizeInputNumber).each(resizeInputNumber);
    $('input[type="number"]').change(resizeInputNumber).each(resizeInputNumber);
    $('textarea').keyup(resizeTextarea).each(resizeTextarea);
    $('select').keyup(resizeTextarea).each(resizeTextarea);

    if (location.href.includes("/correction")) {
            setTimeout(function () {
                $('input[type="text"]').keyup(resizeInput).each(resizeInput); //field_model_col
                $('input[type="text"]').change(resizeInput).each(resizeInput);
                $('input[type="search"]').keyup(resizeInput).each(resizeInput);
                $('input[type="search"]').change(resizeInput).each(resizeInput);
                // $('input[type="search"]').each(function () {
                //     $(this).attr('size', 54);
                // });
                $('input[type="number"]').keyup(resizeInputNumber).each(resizeInputNumber);
                $('input[type="number"]').change(resizeInputNumber).each(resizeInputNumber);
                $('textarea').keyup(resizeTextarea).each(resizeTextarea);
                $('select').keyup(resizeTextarea).each(resizeTextarea);
            },1000);
        }

    $(".datetimepicker-input").focusin( function()
        {
        	$(this).closest('.table-responsive').removeClass('table-responsive').addClass('temp');
        }).focusout(function() {
            $(this).closest('.temp').addClass('table-responsive').removeClass('temp');
        });

});
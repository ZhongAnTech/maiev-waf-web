var policy = null;
var rules = null;
var request_rules = [];
var response_rules = [];
var response_header_rules = [];

var DEFAULT_ACTIONS = [
    {'value': 'DENY'},
    {'value': 'DROP'},
    {'value': 'REDIRECT'},
    {'value': 'ACCEPT'}
];
var REQUEST_ACTIONS = [
    {'value': 'DENY'},
    {'value': 'DROP'},
    {'value': 'REDIRECT'},
    {'value': 'ACCEPT'},
    {'value': 'DEFAULT'}
    //{'value': 'GSUB'},
];
var RESPONSE_HEADER_ACTIONS = [
    {'value': 'DENY'},
    {'value': 'DROP'},
    {'value': 'ACCEPT'}
];
var RESPONSE_BODY_ACTIONS = [
    {'value': 'EMPTY'},
    {'value': 'GSUB'},
    {'value': 'ACCEPT'}
];

function getQueryVariable(variable)
{
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i=0;i<vars.length;i++) {
            var pair = vars[i].split("=");
            if(pair[0] == variable){return pair[1];}
    }
    return(false);
}

function init_policy(){
    var policy_id = $('#uuid').val();
    $("#default_action").selectize({
        maxItems: 1,
        valueField: 'value',
        labelField: 'value',
        searchField: ['value'],
        options: DEFAULT_ACTIONS
    });
    $("#default_action")[0].selectize.on('change', function(){
        var rule_action = $("#default_action")[0].selectize.items[0];
        if(rule_action == 'ACCEPT' || rule_action == 'DROP' || rule_action == 'DENY' ){
            $('.default-redirect-url').hide();
            $('.default-gsub').hide();
        }else if(rule_action == 'REDIRECT'){
            $('.default-redirect-url').show();
            $('.default-gsub').hide();
        }else if(rule_action == 'GSUB'){
            $('.default-redirect-url').hide();
            $('.default-gsub').show();           
        }
    }); 
    if(policy_id != 'new'){
        $.ajax({
            type: 'GET',
            url: '/waf/api/PolicyEdit/' + policy_id,
            contentType: 'application/json',
            success: function (result) {
                if (result.success){
                    policy = result.data;
                    $('#name').val(policy.name);
                    $('#kind').val(policy.kind);
                    $('#cluster').val(policy.cluster);
                    $('#default_action')[0].selectize.addItem(policy.action);

                    if(policy.upload_file_access == 1){
                        $('#upload_file_access').prop('checked', true);
                    }else{
                        $('#upload_file_access').prop('checked', false);
                    }
                    if(policy.request_body_access == 1){
                        $('#request_body_access').prop('checked', true);
                    }else{
                        $('#request_body_access').prop('checked', false);
                    }
                    $('#request_body_limit').val(policy.request_body_limit);                 
                    $('#request_body_nofile_limit').val(policy.request_body_nofile_limit); 
                    if(policy.response_body_access == 1){
                        $('#response_body_access').prop('checked', true);
                    }else{
                        $('#response_body_access').prop('checked', false);
                    }
                    $('#response_body_mime_type').val(policy.response_body_mime_type);
                    $('#response_body_limit').val(policy.response_body_limit);
                    if(policy.action == 'REDIRECT'){
                        $('#default_redirect_url').val(policy.action_vars.redirect_url);
                    }
                    if(policy.action == 'GSUB'){
                        $('#default_gsub_match').val(policy.action_vars.gsub_match);
                        $('#default_gsub_replace').val(policy.action_vars.gsub_replace);
                    }
                    $('#default_action').trigger('change');
                    load_rules('request');
                    load_rules('response_header');
                    load_rules('response');                    
                }
                else{
                    console.log(result['info']);
                }
            },
            error: function(response){
                console.log(response);
            },
            dataType: "json"
        });       
    }else{
        load_rules('request');
        load_rules('response_header');
        load_rules('response');        
    }      
    $('#default_action').trigger('change');

}

function add_rule(rule, stage){
    if(stage == 'request'){
        var rule_list_line = '<li data-rule-id='+ rule.rule_id +'>\
        <a class="rule-op-link"><i class="drag fa fa-arrows gray"></i></a>\
        <span class="m-l-xs ">' + rule.rule_name +' </span>\
        <span class="action-label label label-default" >'+ rule.rule_action +'</span>\
        <a class="rule-op-link pull-right rule-delete"><i class="fa fa-trash danger"></i></a>\
        <a class="rule-op-link pull-right rule-edit"><i class="fa fa-pencil"></i></a>\
        </li>';
        var exists = false;
        for(var i in request_rules){
            if(rule.rule_id == request_rules[i].rule_id){
                exists = true;
                return;
            }
        }
        if(exists) return;
        request_rules.push(rule);
        $('#request-rule-list').append(rule_list_line);
        //绑定事件
        var new_list = $('#request-rule-list').children('li').last();
        var action_label =  new_list.find('.action-label');
        new_list.data('rule-action', rule.rule_action);
        action_label.html(rule.rule_action);
        if(rule.rule_action != 'DEFAULT'){
            action_label.removeClass('label-default').addClass('label-warning');
        }else{
            action_label.removeClass('label-warning').addClass('label-default');
        }
        bind_rule_action(new_list, '#request_rules');
    }
    if(stage == 'response'){
        var rule_list_line = '<li data-rule-id='+ rule.rule_id +'>\
        <a class="rule-op-link"><i class="drag fa fa-arrows gray"></i></a>\
        <span class="m-l-xs ">' + rule.rule_name +' </span>\
        <span class="action-label label label-warning" >'+ rule.rule_action +'</span>\
        <a class="rule-op-link pull-right rule-delete"><i class="fa fa-trash danger"></i></a>\
        <a class="rule-op-link pull-right rule-edit"><i class="fa fa-pencil"></i></a>\
        </li>';
        var exists = false;
        for(var i in response_rules){
            if(rule.rule_id == response_rules[i].rule_id){
                exists = true;
                return;
            }
        }
        if(exists) return;        
        response_rules.push(rule);
        $('#response-rule-list').append(rule_list_line);
        //绑定事件
        var new_list = $('#response-rule-list').children('li').last();  
        var action_label =  new_list.find('.action-label');
        new_list.data('rule-action', rule.rule_action);
        action_label.html(rule.rule_action);
        if(rule.rule_action != 'DEFAULT'){
            action_label.removeClass('label-default').addClass('label-warning');
        }else{
            action_label.removeClass('label-warning').addClass('label-default');
        }       
        bind_rule_action(new_list, '#response_rules');
    }
    if(stage == 'response_header'){
        var rule_list_line = '<li data-rule-id='+ rule.rule_id +'>\
        <a class="rule-op-link"><i class="drag fa fa-arrows gray"></i></a>\
        <span class="m-l-xs ">' + rule.rule_name +' </span>\
        <span class="action-label label label-warning" >'+ rule.rule_action +'</span>\
        <a class="rule-op-link pull-right rule-delete"><i class="fa fa-trash danger"></i></a>\
        <a class="rule-op-link pull-right rule-edit"><i class="fa fa-pencil"></i></a>\
        </li>';
        var exists = false;
        for(var i in response_header_rules){
            if(rule.rule_id == response_header_rules[i].rule_id){
                exists = true;
                return;
            }
        }
        if(exists) return;
        response_header_rules.push(rule);
        $('#header-rule-list').append(rule_list_line);
        //绑定事件
        var new_list = $('#header-rule-list').children('li').last();
        var action_label =  new_list.find('.action-label');
        new_list.data('rule-action', rule.rule_action);
        action_label.html(rule.rule_action);
        if(rule.rule_action != 'DEFAULT'){
            action_label.removeClass('label-default').addClass('label-warning');
        }else{
            action_label.removeClass('label-warning').addClass('label-default');
        }
        bind_rule_action(new_list, '#response_header_rules');
    }
}
function del_rule(rule_id, stage){
    if(stage == 'request'){
        for(var i in request_rules){
            if(rule_id == request_rules[i].rule_id){
                request_rules.splice(i, 1);// delete 
            }
        }
        $('#request-rule-list').children('li').each(function(){
            if(rule_id == $(this).data('rule-id')){
                $(this).remove();
            }
        });
    }
    if(stage == 'response'){
        for(var i in response_rules){
            if(rule_id == response_rules[i].rule_id){
                response_rules.splice(i, 1);// delete 
            }
        }
        $('#response-rule-list').children('li').each(function(){
            if(rule_id == $(this).data('rule-id')){
                $(this).remove();
            }
        });        
    }   
}
function rule_action_edit(rule_id, stage){
    var rule;
    if(stage == 'request'){
        for(var i in request_rules){
            if(request_rules[i].rule_id == rule_id ){
                rule = request_rules[i];
            }
        }
        $("#rule_action")[0].selectize.clearOptions();
        for(var i in REQUEST_ACTIONS){
            $("#rule_action")[0].selectize.addOption(REQUEST_ACTIONS[i]);
        }

    }
    else if(stage == 'response'){
        for(var i in response_rules){
            if(response_rules[i].rule_id == rule_id ){
                rule = response_rules[i];
            }
        }
        $("#rule_action")[0].selectize.clearOptions();
        for(var i in RESPONSE_BODY_ACTIONS){
            $("#rule_action")[0].selectize.addOption(RESPONSE_BODY_ACTIONS[i]);
        }
    }else if(stage == 'response_header'){
        for(var i in response_header_rules){
            if(response_header_rules[i].rule_id == rule_id ){
                rule = response_header_rules[i];
            }
        }
        $("#rule_action")[0].selectize.clearOptions();
        for(var i in RESPONSE_HEADER_ACTIONS){
            $("#rule_action")[0].selectize.addOption(RESPONSE_HEADER_ACTIONS[i]);
        }
    }
    else return;
    $('#rule_id').val(rule.rule_id);
    $('#rule_stage').val(stage);
    $('#rule_name').val(rule.rule_name);
    $('#rule_action')[0].selectize.addItem(rule.rule_action);
    $('#rule_action').trigger('change');
    if(rule.rule_action == 'REDIRECT'){
        $('#redirect_url').val(rule.action_vars.redirect_url);
    }
    if(rule.rule_action == 'GSUB'){
        $('#gsub_match').val(rule.action_vars.gsub_match);
        $('#gsub_replace').val(rule.action_vars.gsub_replace);
    }
    $("#rule_action_modal").modal();
}
function save_rule_action_edit(){
    $('#rule_action_edit').validator('validate');
    var is_validate = true;
    $('#rule_action_edit').find('.has-error').each(function(){
        if($(this).is(':visible')){
            is_validate = false;
            return;
        }
    });
    if(is_validate){
        var rule_action = $("#rule_action_edit").serializeObject();
        var action_label =  $('li[data-rule-id="'+ rule_action.rule_id +'"]').find('.action-label');
        action_label.html(rule_action.rule_action);
        if(rule_action.rule_action != 'DEFAULT'){
            action_label.removeClass('label-default').addClass('label-warning');
        }else{
            action_label.removeClass('label-warning').addClass('label-default');
        }
        rule_action.action_vars = {}
        if(rule_action.rule_action == 'REDIRECT'){
            rule_action.action_vars.redirect_url = rule_action.redirect_url;
            delete rule_action.redirect_url;
        }
        if(rule_action.rule_action == 'GSUB'){
            rule_action.action_vars.gsub_match = rule_action.gsub_match;
            rule_action.action_vars.gsub_replace = rule_action.gsub_replace;
            delete rule_action.gsub_match;
            delete rule_action.gsub_replace;
        }
        if(rule_action.rule_stage == 'request'){
            for(var i in request_rules){
                if(request_rules[i].rule_id == rule_action.rule_id){
                    request_rules[i] = rule_action;                  
                }
            }
        }
        if(rule_action.rule_stage == 'response'){
            for(var i in response_rules){
                if(response_rules[i].rule_id == rule_action.rule_id){
                    response_rules[i] = rule_action;
                }
            }
        }
        if(rule_action.rule_stage == 'response_header'){
            for(var i in response_header_rules){
                if(response_header_rules[i].rule_id == rule_action.rule_id){
                    response_header_rules[i] = rule_action;
                }
            }
        }
        $("#rule_action_modal").modal('hide');
    }
}

function save_policy(){
    $('#policy_form').validator('validate');
    var is_validate = true;
    $('#policy_form').find('.has-error').each(function(){
        if($(this).is(':visible')){
            is_validate = false;
            return;
        }
    }); 
    if(is_validate){
        $("#save_policy").attr("disabled",true);
        var policy_data = $("#policy_form").serializeObject();
        var policy = {
            'uuid': policy_data.uuid,
            'name': policy_data.name,
            'kind': policy_data.kind,
            'cluster': policy_data.cluster,
            'action': policy_data.default_action,
            'upload_file_access': $('#upload_file_access').prop('checked')? 1:0,
            'request_body_access': $('#request_body_access').prop('checked')? 1:0,
            'request_body_limit': policy_data.request_body_limit,
            'request_body_nofile_limit': policy_data.request_body_nofile_limit,
            'response_body_access': $('#response_body_access').prop('checked')? 1:0,
            'response_body_mime_type': policy_data.response_body_mime_type,
            'response_body_limit': policy_data.response_body_limit
        };
        policy.action_vars = {};
        if(policy_data.default_action == 'REDIRECT'){
            policy.action_vars.redirect_url = policy_data.default_redirect_url;
        }
        if(policy_data.default_action == 'GSUB'){
            policy.action_vars.gsub_match = policy_data.default_gsub_match;
            policy.action_vars.gsub_replace = policy_data.default_gsub_replace;
        }
        policy.request_filters = [];
        policy.response_filters = [];
        policy.response_header_filters = [];
        $('#request-rule-list').children('li').each(function(){
            var rule_id = $(this).data('rule-id');
            for(var i in request_rules){
                if(rule_id == request_rules[i].rule_id){
                    policy.request_filters.push(request_rules[i]);
                }
            }
        });
        $('#response-rule-list').children('li').each(function(){
            var rule_id = $(this).data('rule-id');
            for(var i in response_rules){
                if(rule_id == response_rules[i].rule_id){
                    policy.response_filters.push(response_rules[i]);
                }
            }
        });
        $('#header-rule-list').children('li').each(function(){
            var rule_id = $(this).data('rule-id');
            for(var i in response_header_rules){
                if(rule_id == response_header_rules[i].rule_id){
                    policy.response_header_filters.push(response_header_rules[i]);
                }
            }
        });

        $.ajax({
            type: 'POST',
            url: '/waf/api/PolicyEdit/' + policy.uuid,
            contentType: 'application/json',
            success: function (result) {
                if (result.success){
                    $("#save_policy").attr("disabled", false);
                    toastr.success('成功', '提交成功');
                    setTimeout(() => {
                        location.href = "/Policy";
                    }, 1000);
                }
                else{
                    $("#save_policy").attr("disabled", false);
                    toastr.error('错误', result['info']);
                }
            },
            error: function(response){
                $("#save_policy").attr("disabled", false);
                toastr.error('错误', '服务端异常');
            },
            dataType: "json",
            data: JSON.stringify(policy)
        });        
    }   
}

function load_rules(stage){
    $.ajax({
        type: 'GET',
        url: '/waf/api/PolicyRules?stage=' + stage,
        contentType: 'application/json',
        success: function (result) {
            if (result.success){
                init_rules(result.data, stage);
            }else{
                console.log('load rules failed ,' + result.info )
            }
        },
        error: function(error){
            conosle.log('failed to load rules' + error)
        },
        dataType: "json"
    });     
}

function init_rules(data, stage){
    rules = data;
    $("ol#request-rule-list").sortable({
        handle: 'i.drag'
    });
    $("ol#response-rule-list").sortable({
        handle: 'i.drag'
    });
    $("ol#header-rule-list").sortable({
        handle: 'i.drag'
    });
    var select_data = [];
    for(var i in data){
        var item = {
            'value': data[i].id,
            'text': data[i].f_rule_name
        }
        select_data.push(item);
    }
    if(stage == 'request'){
        var request_select = $('#request_rules').multipleSelect({
            "data-locale": 'zh-CN',
            placeholder: '选择规则',
            filter: true,
            data: select_data,
            selectAll: false,
            onClick: function(view) {
                if(view.checked){
                    var is_in_list = false;
                    $('#request-rule-list').children('li').each(function(){
                       var rule_id = $(this).data('rule-id');
                       if(rule_id == view.value){
                           is_in_list = true;
                           return;
                       }
                    });
                    if(is_in_list == false){
                        var rule = {
                            'rule_id': view.value,
                            'rule_name': view.label,
                            'rule_action': 'DEFAULT',
                            'action_vars': {}
                        };
                        add_rule(rule, stage);
                    }
                }else{
                    del_rule(view.value, stage);
                }
            }
        });
        if(policy){
            console.log(policy.request_filters);
            for(var i in policy.request_filters){
                request_select.multipleSelect('check', policy.request_filters[i].rule_id);
                add_rule(policy.request_filters[i], 'request');
            } 
        }
    }
    if(stage == 'response'){
        var response_select = $('#response_rules').multipleSelect({
            "data-locale": 'zh-CN',
            placeholder: '选择规则',
            filter: true,
            data: select_data,
            selectAll: false,
            onClick: function(view) {
                if(view.checked){
                    var is_in_list = false;
                    $('#response-rule-list').children('li').each(function(){
                       var rule_id = $(this).data('rule-id');
                       if(rule_id == view.value){
                           is_in_list = true;
                           return;
                       }
                    });
                    if(is_in_list == false){
                        var rule = {
                            'rule_id': view.value,
                            'rule_name': view.label,
                            'rule_action': 'EMPTY',
                            'action_vars': {}
                        };
                        add_rule(rule, stage);
                    }
                }else{
                    del_rule(view.value, stage);
                }
            }
        });
        if(policy){
            for(var i in policy.response_filters){
                response_select.multipleSelect('check', policy.response_filters[i].rule_id);
                add_rule(policy.response_filters[i], 'response');
            } 
        }
    }
    if(stage == 'response_header'){
        var response_header_rules = $('#response_header_rules').multipleSelect({
            "data-locale": 'zh-CN',
            placeholder: '选择规则',
            filter: true,
            data: select_data,
            selectAll: false,
            onClick: function(view) {
                if(view.checked){
                    var is_in_list = false;
                    $('#header-rule-list').children('li').each(function(){
                       var rule_id = $(this).data('rule-id');
                       if(rule_id == view.value){
                           is_in_list = true;
                           return;
                       }
                    });
                    if(is_in_list == false){
                        var rule = {
                            'rule_id': view.value,
                            'rule_name': view.label,
                            'rule_action': 'DENY',
                            'action_vars': {}
                        };
                        add_rule(rule, stage);
                    }
                }else{
                    del_rule(view.value, stage);
                }
            }
        });
        if(policy){
            for(var i in policy.response_header_filters){
                response_header_rules.multipleSelect('check', policy.response_header_filters[i].rule_id);
                add_rule(policy.response_header_filters[i], 'response_header');
            }
        }
    }
}

function bind_rule_action(item, select_dom_id){
    item.children('a.rule-delete').on('click', function(){
        var list_obj = $(this).parents('li');
        var rule_id = list_obj.data('rule-id');
        $(select_dom_id).multipleSelect('uncheck', rule_id);
        list_obj.remove();
    });
    item.children('a.rule-edit').on('click', function(){
        var list_obj = $(this).parents('li');
        console.log(list_obj.parents('ol').attr('id'));
        var rule_id = list_obj.data('rule-id');
        var stage = 'request';
        if(list_obj.parents('ol').attr('id') == 'request-rule-list'){
            stage = 'request';
        }
        if(list_obj.parents('ol').attr('id') == 'header-rule-list'){
            stage = 'response_header';
        }
        if(list_obj.parents('ol').attr('id') == 'response-rule-list'){
            stage = 'response';
        }
        rule_action_edit(rule_id, stage);
    });
}
$(document).ready(function() {
    $("#rule_action").selectize({
        maxItems: 1,
        valueField: 'value',
        labelField: 'value',
        searchField: ['value'],
        options: REQUEST_ACTIONS
    });
    $("#rule_action")[0].selectize.on('change', function(){
        var rule_action = $("#rule_action")[0].selectize.items[0];
        if(rule_action == 'DEFAULT' || rule_action == 'ACCEPT' || rule_action == 'DROP' || rule_action == 'EMPTY' || rule_action == 'DENY' ){
            $('.redirect-url').hide();
            $('.gsub').hide();
        }else if(rule_action == 'REDIRECT'){
            $('.redirect-url').show();
            $('.gsub').hide();
        }else if(rule_action == 'GSUB'){
            $('.redirect-url').hide();
            $('.gsub').show();
        }
    });
    $('#save_policy').on('click', function(){save_policy();});
    $('#save_rule_action').on('click', function(){save_rule_action_edit();});
    $('.redirect-url').hide();
    $('.gsub').hide();
    init_policy();


});

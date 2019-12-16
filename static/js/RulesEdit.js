var rule = [];

var REQUEST_FIELDS = [
            {id: 'URI', title: 'URI'},
            {id: 'IP', title: 'IP'},
            {id: 'HOST', title: 'HOST'},
            {id: 'METHOD', title: 'METHOD'},
            {id: 'USERAGENT', title: 'USERAGENT'},
            {id: 'REFERER', title: 'REFERER'},
            {id: 'ALL_ARGS', title: 'ALL_ARGS'},
            {id: 'ALL_ARGS_NAMES', title: 'ALL_ARGS_NAMES'},
            {id: 'ALL_ARGS_COMBINED_SIZE', title: 'ALL_ARGS_COMBINED_SIZE'},
            {id: 'URL_ARGS', title: 'URL_ARGS'},
            {id: 'URL_ARGS_NAMES', title: 'URL_ARGS_NAMES'},
            {id: 'BODY_ARGS', title: 'BODY_ARGS'},
            {id: 'BODY_ARGS_NAMES', title: 'BODY_ARGS_NAMES'},
            {id: 'BODY', title: 'BODY'},
            {id: 'BODY_LENGTH', title: 'BODY_LENGTH'},
            {id: 'COOKIES', title: 'COOKIES'},
            {id: 'COOKIES_NAMES', title: 'COOKIES_NAMES'},
            {id: 'HEADERS', title: 'HEADERS'},
            {id: 'HEADERS_NAMES', title: 'HEADERS_NAMES'},
            {id: 'FILES_NAMES', title: 'FILES_NAMES'},
            {id: 'FILES_TMP_CONTENT', title: 'FILES_TMP_CONTENT'}
        ];
var RESP_HEADER_FIELDS = [
            {id: 'URI', title: 'URI'},
            {id: 'IP', title: 'IP'},
            {id: 'HOST', title: 'HOST'},
            {id: 'METHOD', title: 'METHOD'},
            {id: 'USERAGENT', title: 'USERAGENT'},
            {id: 'REFERER', title: 'REFERER'},
            {id: 'ALL_ARGS', title: 'ALL_ARGS'},
            {id: 'ALL_ARGS_NAMES', title: 'ALL_ARGS_NAMES'},
            {id: 'ALL_ARGS_COMBINED_SIZE', title: 'ALL_ARGS_COMBINED_SIZE'},
            {id: 'URL_ARGS', title: 'URL_ARGS'},
            {id: 'URL_ARGS_NAMES', title: 'URL_ARGS_NAMES'},
            {id: 'BODY_ARGS', title: 'BODY_ARGS'},
            {id: 'BODY_ARGS_NAMES', title: 'BODY_ARGS_NAMES'},
            {id: 'BODY', title: 'BODY'},
            {id: 'BODY_LENGTH', title: 'BODY_LENGTH'},
            {id: 'COOKIES', title: 'COOKIES'},
            {id: 'COOKIES_NAMES', title: 'COOKIES_NAMES'},
            {id: 'HEADERS', title: 'HEADERS'},
            {id: 'HEADERS_NAMES', title: 'HEADERS_NAMES'},
            {id: 'FILES_NAMES', title: 'FILES_NAMES'},
            {id: 'FILES_TMP_CONTENT', title: 'FILES_TMP_CONTENT'},
            {id: 'RESPONSE_STATUS', title: 'RESPONSE_STATUS'},
            {id: 'RESPONSE_HEADERS', title: 'RESPONSE_HEADERS'},
            {id: 'RESPONSE_HEADERS_NAMES', title: 'RESPONSE_HEADERS_NAMES'},
            {id: 'RESPONSE_PROTOCOL', title: 'RESPONSE_PROTOCOL'}
    ];

var RESP_BODY_FIELDS = [
            {id: 'URI', title: 'URI'},
            {id: 'IP', title: 'IP'},
            {id: 'HOST', title: 'HOST'},
            {id: 'METHOD', title: 'METHOD'},
            {id: 'USERAGENT', title: 'USERAGENT'},
            {id: 'REFERER', title: 'REFERER'},
            {id: 'ALL_ARGS', title: 'ALL_ARGS'},
            {id: 'ALL_ARGS_NAMES', title: 'ALL_ARGS_NAMES'},
            {id: 'ALL_ARGS_COMBINED_SIZE', title: 'ALL_ARGS_COMBINED_SIZE'},
            {id: 'URL_ARGS', title: 'URL_ARGS'},
            {id: 'URL_ARGS_NAMES', title: 'URL_ARGS_NAMES'},
            {id: 'BODY_ARGS', title: 'BODY_ARGS'},
            {id: 'BODY_ARGS_NAMES', title: 'BODY_ARGS_NAMES'},
            {id: 'BODY', title: 'BODY'},
            {id: 'BODY_LENGTH', title: 'BODY_LENGTH'},
            {id: 'COOKIES', title: 'COOKIES'},
            {id: 'COOKIES_NAMES', title: 'COOKIES_NAMES'},
            {id: 'HEADERS', title: 'HEADERS'},
            {id: 'HEADERS_NAMES', title: 'HEADERS_NAMES'},
            {id: 'FILES_NAMES', title: 'FILES_NAMES'},
            {id: 'FILES_TMP_CONTENT', title: 'FILES_TMP_CONTENT'},
            {id: 'RESPONSE_STATUS', title: 'RESPONSE_STATUS'},
            {id: 'RESPONSE_BODY', title: 'RESPONSE_BODY'},
            {id: 'RESPONSE_BODY_LENGTH', title: 'RESPONSE_BODY_LENGTH'},
            {id: 'RESPONSE_HEADERS', title: 'RESPONSE_HEADERS'},
            {id: 'RESPONSE_HEADERS_NAMES', title: 'RESPONSE_HEADERS_NAMES'},
            {id: 'RESPONSE_PROTOCOL', title: 'RESPONSE_PROTOCOL'}
        ];


function init_form(){

    var nid = $('#nid').val()
    var url = '/waf/api/Rules/'+ nid;
    if (nid=='new'){
        $("#rules_action").html('规则添加');
        $("#rule_id_div").attr("hidden","");
    }else {
        $.ajax({
        type: 'GET',
        url: url,
        contentType: 'application/json',
        success: function (result) {
            if (result.success){
                $("#f_id").val(result.data.id);
                $("#f_rule_id").val(result.data.f_rule_id);
                $("#f_rule_name").val(result.data.f_rule_name);
                $("#f_rule_desc").val(result.data.f_rule_desc);
                $("#tags").val(result.data.tags);
                $("#stage")[0].selectize.addItem(result.data.stage);
                $("#stage")[0].selectize.trigger('change');
                $("#risk_level")[0].selectize.addItem(result.data.risk_level);
                $("#f_rule_name").attr("readonly","")
                //赋值规则
                rule = result.data.f_rule;
                draw_filter_table("#filter_table");

            }
            else{
                toastr.error('错误',result['info'])
            }
        },
        dataType: "json"
        });
    }
}


//绘制或者更新过滤器表格
function draw_filter_table(tableSel){
    var table_data = [];
    for(var i in rule){
        var tmp = [
            rule[i].filter_id,
            rule[i].items,
            rule[i].transforms,
            rule[i].operator,
            rule[i].value
        ]
        table_data.push(tmp);
    }

    var table_obj = $(tableSel).DataTable({
        data: table_data,
        searching: false,
        destroy: true,
        bInfo: false, //是否显示分页信息
        paging: false,
        columns: [
             { "title": "filter_id","class":"center"},
             { "title": "items" ,"class":"center"},
             { "title": "transforms" ,"class":"center"},
             { "title": "operator","class":"center"},
             { "title": "value" ,"class":"center"}
        ],
        columnDefs:[
            {
                targets:[0],
                visible: false,
                render:function(data, type, row){
                    return htmlEncode(data);
                },
            },
            {
                targets:[1],
                render:function(data, type, row){
                    return htmlEncode(data);
                },
            },
            {
                targets:[2],//tags
                render:function(data, type, row){
                    return htmlEncode(data);
                    //var htmlStr = "";
                    //for(var i in data){
                    //    htmlStr += '<span style="display: inline-block;" class="label label-xs label-info">' + htmlEncode(data); + '</span>';
                    //}
                    //return htmlStr;
                }
            },
            {
                targets:[3],
                render:function(data, type, row){
                    return htmlEncode(data);
                },
            },
            {
                targets:[4],
                render:function(data, type, row){
                    if(row[3] == 'REG' || row[3] == 'NRE'){
                        return htmlEncode(window.atob(data));
                    }
                    else return htmlEncode(data);
                },
            },
            {
                targets:[5],
                class:"center",
                render:function(data, type, row){
                    var htmlStr = "<a class=\"btn btn-info btn-xs \" data-id=\""+row[0] +"\" onclick=\"filter_edit('"+ row[0] +"')\"><i class=\"fa fa-pencil\"></i> 修改 </a> ";
                    htmlStr += " <a class=\"btn btn-danger btn-xs \" data-id=\""+row[0] +"\" onclick=\"filter_trash('"+ row[0] +"')\"><i class=\"fa fa-trash-o\"></i> 删除 </a> ";
                    return htmlStr;
                },
                "ordering": false
            }
        ],
        "initComplete": function(settings, json) {
        }
    });
    return table_obj;
}

//保存过滤规则
function save_filter(){
    filter_var = $("#filter_edit").serializeObject();
    filter_var.items = $("#items")[0].selectize.items;
    filter_var.transforms = $("#transforms")[0].selectize.items;
    if(filter_var.operator == "" || filter_var.value == ""){
        alert("比较方法和比较值不能为空！");
        return;
    }
    if(filter_var.operator == 'REG' || filter_var.operator == 'NRE'){
        filter_var.value = window.btoa(filter_var.value);
    }
    $("#filter_modal").modal("hide");
    if(filter_var.filter_id == "0"){
        //新增过滤器规则
        filter_var.filter_id = guid();
        rule.push(filter_var);
    }else{
        //更新过滤器规则
        for(var i in rule){
            if(rule[i].filter_id == filter_var.filter_id){
                rule[i] = filter_var;
            }
        }
    }
    //重绘表格
    draw_filter_table("#filter_table");
}

function filter_edit(filter_id){
    for(var i in rule){
        if(rule[i].filter_id == filter_id){
            $("#filter_id").val(htmlEncode(rule[i].filter_id));
            $("#items")[0].selectize.clear();
            $("#items")[0].selectize.addItem(rule[i].column);
            $("#items")[0].selectize.trigger('change');
            for(var item in rule[i].items){
                $("#items")[0].selectize.addItem(rule[i].items[item]);
                $("#items")[0].selectize.trigger('change');
            }
            $("#transforms")[0].selectize.clear();
            for(var item in rule[i].transforms){
                $("#transforms")[0].selectize.addItem(rule[i].transforms[item]);
                $("#transforms")[0].selectize.trigger('change');
            }
            $("#operator")[0].selectize.addItem(rule[i].operator);
            if(rule[i].operator == 'REG' || rule[i].operator == 'NRE'){
                $("#value").val(window.atob(rule[i].value));    
            }else{
                $("#value").val(rule[i].value);
            }
            $("#filter_modal").modal();
        }
    }
};

function filter_trash(filter_id){
    for(var i in rule){
        if(rule[i].filter_id == filter_id){
            //删除元素
            rule.splice(i,1);
        }
    }
    //重绘表格
    draw_filter_table("#filter_table");
};


//提交规则
function save_rule(){
    $("#rule_form").validator('validate');
    if($('#w_rule_form_1').find('.has-error').length) {
        alert("请将规则填写完整!");
        return;
    }
    full_rule = $("#rule_form").serializeObject();

    // if(full_rule.f_rule_status == "on"){
    //     full_rule.f_rule_status = 1;
    // }else{
    //     full_rule.f_rule_status = 0;
    // }
    full_rule.f_rule = rule;
    $("#save_rule").attr("disabled",true);

    var nid = $('#nid').val();
    var url = "/waf/api/Rules/"+ nid;
    if (nid == 'new'){
        url = "/waf/api/Rules";
    };
    $.ajax({
        type: 'POST',
        url: url,
        contentType: 'application/json',
        data: JSON.stringify(full_rule),
        success: function (res) {
            console.log(res);
            if (res.success){
                $("#save_rule").attr("disabled",false);
                // location.reload();
                location.href = "/Rules";
            }
            else{
                toastr.error('错误',res['info']);
                $("#save_rule").attr("disabled",false);
            }
        },
        dataType: "json"
    });
}

$(document).ready(function() {

    //初始化select2
    $(".transforms_select").selectize({
        maxItems: 20
    });

    $(".multi_select").selectize(
        {
            maxItems: 20
        }       
    );

    $("#items").selectize({
        maxItems: 20,
        valueField: 'id',
        labelField: 'title',
        searchField: ['title'],
        options: REQUEST_FIELDS
    });
    $("#stage").on('change', function(){
        var stage = $('#stage').val();
        if(stage == 'request'){
            $("#items")[0].selectize.clearOptions();
            for(var i in REQUEST_FIELDS){
                $("#items")[0].selectize.addOption(REQUEST_FIELDS[i]);
            }
        }
        if(stage == 'response_header'){
            $("#items")[0].selectize.clearOptions();
            for(var i in RESP_HEADER_FIELDS){
                $("#items")[0].selectize.addOption(RESP_HEADER_FIELDS[i]);
            }
        }
        if(stage == 'response'){
            $("#items")[0].selectize.clearOptions();
            for(var i in RESP_BODY_FIELDS){
                $("#items")[0].selectize.addOption(RESP_BODY_FIELDS[i]);
            }
        }
    });

    $(".single_select").selectize(      
    );   
    //初始化表格
    draw_filter_table("#filter_table");

    //绑定添加过滤规则的事件
    $("#add_filter").on("click",function(){
        $("#filter_id").val(htmlEncode('0'));
        $("#transforms")[0].selectize.clear();
        //trigger_items_display();
        $("#filter_modal").modal();
    });

    //绑定选定特定column的显示
    $("#items").on("change",function(){
        //trigger_items_display();
    })
    //绑定保存过滤规则事件
    $("#save_filter").on("click",function(){
        save_filter();
    });
    //绑定规则保存事件
    $("#save_rule").on("click",function(){
        save_rule();
    });
    //初始化表单
    init_form();
});

var waf = new AppPage();

function rule_edit(nid){
    var data = null;
    $('#w_rule_form_1')[0].reset();
    $("#site")[0].selectize.clear();
    if (nid){
        $.getJSON("/waf/api/Whitelist/"+nid,function(result){
            $('#cert_edit_title').html(htmlEncode('修改白名单'));
            if (result['success']){
                data = result['data'];
                $("#nid").val(nid);
                $("#w_rule_desc").val(htmlEncode(data.rule_desc));
                $("#w_url").val(htmlEncode(data.rule.URI?data.rule.URI : ''));
                $("#w_ip").val(htmlEncode(data.rule.IP?data.rule.IP : ''));
                $("#w_host").val(htmlEncode(data.rule.HOST?data.rule.HOST : ''));
                if (data.status == 1){
                    $('#w_rule_status').attr("checked","")
                }else {
                    $('#w_rule_status').removeAttr("checked")
                }
                for (var s in data.webs){
                    $("#site")[0].selectize.addItem(data.webs[s].nid);
                    // $("#site")[0].selectize.disable();
                };
                $("#edit_modal").modal();

            }
            else {
                toastr.error('错误',result['info'])
            }
        });
    }else {
        $('#cert_edit_title').html(htmlEncode('添加白名单'));
        $("#site")[0].selectize.enable();
    }
    $('#edit_modal').modal();
};

function rule_disable(nid){
    $("#w_op_2").val("POST");
    $("#id_2").val(nid);
    $("#w_rule_status_2").val(-1);
    $("#op_rule").attr("disabled",false);
    $("#notify_box").html("确认禁用该白名单规则?");
    $("#notify_modal").modal();
};
function rule_enable(nid){
    $("#w_op_2").val("POST");
    $("#id_2").val(nid);
    $("#w_rule_status_2").val(1);
    $("#op_rule").attr("disabled",false);
    $("#notify_box").html("确认启用该白名单规则?");
    $("#notify_modal").modal();
};
function rule_trash(nid){
    $("#id_2").val(nid);
    $("#w_op_2").val("DELETE");
    $("#op_rule").attr("disabled",false);
    $("#notify_box").html("确认删除该白名单规则?");
    $("#notify_modal").modal();
};


function save_rule() {
    var data = $("#w_rule_form_1").serializeObject();
    if(data.w_rule_status == "on")  data.w_rule_status = 1
    else data.w_rule_status = -1;
    data.nid = $('#nid').val();
    var sites = [];
    $("#site").each(function(){
    var vals = $(this).val();
    if (vals != ""){
        console.log(vals);
        sites.push(vals);
    };});
    data.site = sites[0];
    var url = '/waf/api/Whitelist';
    if (data.nid){
        url = '/waf/api/Whitelist/'+data.nid
    }
    $.ajax({
        type: 'POST',
        url: url,
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (res) {
            console.log(res);
            if (res.success){
                location.reload();
            }
            else{
                toastr.error('错误',res['info'])
            }
        },
        dataType: "json"
    });

}


$(document).ready(function() {

    draw_table();





    $("#save_op").on("click",function(){
        var url = '/waf/api/Whitelist/'+$("#id_2").val();
        var type = $("#w_op_2").val();
        $.ajax({
            type: type,
            url: url,
            contentType: 'application/json',
            data: JSON.stringify({"w_rule_status": Number($("#w_rule_status_2").val())}),
            success: function (res) {
                console.log(res);
                if (res.success){
                    location.reload();
                }
                else{
                    toastr.error('错误',res['info'])
                }
            },
            dataType: "json"
        });
    });


});



function draw_table() {
    $('#whitelist_table').DataTable({
        "serverSide": true,
        "processing": true,
        "bAutoWidth" : true,
        paging : true,
        pagingType : "simple_numbers",
        bLengthChange: false,
        ajax : function(data, callback, settings) {
            $.ajax({
                type : "GET",
                url : "/waf/api/Whitelist",
                cache : true, //禁用缓存
                data : {'start': data.start, 'size': 10, 'draw': data.draw},
                dataType : "json",
                success : function(res) {
                    if(res.success){
                    //setTimeout仅为测试遮罩效果
                    setTimeout(function() {
                        //封装返回数据，这里仅演示了修改属性名
                        var returnData = {};
                        returnData.draw = res.data.pages.draw;//这里直接自行返回了draw计数器,应该由后台返回
                        returnData.recordsTotal = res.data.pages.total;
                        returnData.recordsFiltered = res.data.pages.total;
                        returnData.data = res.data.whitelist;
                        //关闭遮罩
                        //$wrapper.spinModal(false);
                        //调用DataTables提供的callback方法，代表数据已封装完成并传回DataTables进行渲染
                        //此时的数据需确保正确无误，异常判断应在执行此回调前自行处理完毕

                        $("#site").selectize({
                            persist: false,
                            maxItems:100,
                            valueField:'nid',
                            labelField: 'name',
                            options:res.data.sites,

                        });

                        callback(returnData);
                        },500);
                    }else {toastr.error('错误',res.info)}},
                error : function(XMLHttpRequest,textStatus,errorThrown) {
                    toastr.error('错误','后端服务异常')
                }});
            },
        searching: false,
        ordering:  false,
        bInfo: false,
        columns:[
            {
                data: 'time',
                "title": "时间",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){
                    var html_str = '';
                    html_str = new Date(parseInt(data) * 1000).toLocaleString();
                    return html_str;
                },
            },
            {
                data: 'rule_desc',
                "title": "描述",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){

                    return data;
                },
                "ordering": false
            },
            {
                data: 'rule',
                "title": "内容",
                "class":"center",
                "width":"20%",
                render:function(data,type,full,row){
                        var cell_html = '<dl class="dl-horizontal">';
                            for(var p in data){
                                if(data[p] !== ""){
                                    cell_html += '<dt>'+ htmlEncode(p) +'</dt>';
                                    cell_html += '<dd>'+ htmlEncode(data[p]) +'</dd>';
                                }

                            }
                        cell_html += '</dl>';
                        return cell_html;
                    },
                "ordering": false
            },
            {
                data: 'nid',
                "title": "站点",
                "class":"center",
                "width":"15%",
                render:function(data,type,full,row){
                    var htmlStr = '';
                    return htmlStr;
                },
                "ordering": false
            },
            {
                data: 'status',
                "title": "状态",
                "class":"center",
                "width":"10%",
                render:function(data,type,full,row){
                        var html_str = "";
                        if(data==-1){
                            html_str = "<td><span class=\"label label-default\">停用</span></td>";
                        }
                        if(data==1){
                            html_str = "<td><span class=\"label label-success\">启用</span></td>";
                        }
                        return html_str
                    },
                "ordering": false
            },
            {
                data: 'nid',
                "title": "操作",
                "class":"center",
                "width":"25%",
                render:function(data,type,full,row){
                        var htmlStr = "<a class=\"btn btn-info btn-xs \" data-id=\""+data +"\" onclick=\"rule_edit('"+ data +"')\"><i class=\"fa fa-pencil\"></i> 修改 </a> ";
                        if(full.status == 1) htmlStr += " <a class=\"btn btn-warning btn-xs \" data-id=\""+data +"\" onclick=\"rule_disable('"+ data +"')\"><i class=\"fa fa-stop\"></i> 停用 </a> ";
                        if(full.status == -1){
                            htmlStr += " <a class=\"btn btn-success btn-xs \" data-id=\""+data +"\" onclick=\"rule_enable('"+ data +"')\"><i class=\"fa fa-pay\"></i> 启用 </a> ";
                            htmlStr += " <a class=\"btn btn-danger btn-xs \" data-id=\""+data +"\" onclick=\"rule_trash('"+ data +"')\"><i class=\"fa fa-trash-o\"></i> 删除 </a> ";
                        }
                        return htmlStr;

                    }
,
                "ordering": false
            }
        ],

    });

}


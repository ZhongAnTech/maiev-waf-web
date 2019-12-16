

function rule_edit(nid){
    location.href = "/Rules/"+nid;
};

function rule_disable(nid){
    $("#op").val("PUT");
    $("#id").val(nid);
    $("#status").val(0);
    $("#notify_box").html("确认禁用该规则?");
    $("#notify_modal").modal();
};
function rule_enable(id){
    $("#op").val("PUT");
    $("#id").val(id);
    $("#status").val(1);
    $("#notify_box").html("确认启用该规则?");
    $("#notify_modal").modal();
};
function rule_trash(id){
    $("#op").val("POST");
    $("#id").val(id);
    $("#status").val(-1);
    $("#notify_box").html("确认删除该规则?");
    $("#notify_modal").modal();
};


function op_confirm(){
    var url = '/waf/api/Rules/'+$("#id").val();
    var type = $("#op").val();
    $.ajax({
        type: type,
        url: url,
        contentType: 'application/json',
        data: JSON.stringify({"status": $("#status").val()}),
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





$(document).ready( function () {

    $("#op_confirm").on("click",function(){
        op_confirm();
    });

    var rules_table = draw_table();
    $("#stage-select").on("change", function(){
        rules_table.ajax.reload();
    })
} );

function draw_table() {
    return $('#rules_table').DataTable({
        "serverSide": true,
        "processing": true,
        "bAutoWidth" : true,
        paging : true,
        pagingType : "simple_numbers",
        bLengthChange: false,
        ajax : function(data, callback, settings) {
            var stage = $("#stage-select").val();
            if(stage == "ALL") stage = null;
            $.ajax({
                type : "GET",
                url : "/waf/api/Rules",
                cache : true, //禁用缓存
                data : {'start': data.start, 'stage': stage,'search': data.search.value, 'size': 10, 'draw': data.draw},
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
                        returnData.data = res.data.rule;
                        //关闭遮罩
                        //$wrapper.spinModal(false);
                        //调用DataTables提供的callback方法，代表数据已封装完成并传回DataTables进行渲染
                        //此时的数据需确保正确无误，异常判断应在执行此回调前自行处理完毕
                        callback(returnData);
                        },500);
                    }else {toastr.error('错误',res.info)}},
                error : function(XMLHttpRequest,textStatus,errorThrown) {
                    toastr.error('错误','后端服务异常')
                }});
            },
        searching: true,
        ordering:  false,
        bInfo: false,
        columns:[
            {
                data: 'id',
                "title": "id",
                "class":"center",
                "visible": false,
                "searchable": false,
            },
            {
                data: 'id',
                "title": "规则ID",
                "class":"center",
                "width":"5%",
                render: function(data,type,full,row){
                    return data;
                },
            },
            {
                data: 'stage',
                "title": "阶段",
                "class":"center",
                "width":"5%",
                render: function(data,type,full,row){
                    if(data == 'request') return "请求阶段";
                    if(data == 'response') return "响应体阶段";
                    if(data == 'response_header') return "响应头阶段";
                },
            },            
            {
                data: 'gmt_modify',
                "title": "编辑时间",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){
                    var html_str = '';
                    html_str = new Date(parseInt(data) * 1000).toLocaleString();
                    return html_str;
                },
            },
            {
                data: 'f_rule_name',
                "title": "规则名",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){

                    return data;
                },
                "ordering": false
            },
            {
                data: 'f_rule_desc',
                "title": "规则描述",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){
                    return data;
                },
                "ordering": false
            },
            {
                data: 'tags',
                "title": "TAGS",
                "class":"center",
                "width":"10%",
                render:function(data, type, row){
                    var htmlStr = "";
                    if (data){
                        var data_arr = data.split(",");
                        for(var i in data_arr){
                        htmlStr += '<span style="display: inline-block;" class="label label-xs label-default">' + htmlEncode(data_arr[i]) + '</span> &nbsp;';
                    }
                    }
                    return htmlStr;
                },
                "ordering": false
            },
            {
                data: 'risk_level',
                "title": "风险",
                "class":"center",
                "width":"10%",
                render:function(data, type, row){
                    var htmlStr = '<span style="color:#E18B00">';
                    for(var i=1 ;i<4;i++){
                        if(i <= data){
                            htmlStr += '<i class="fa fa-star"></i>&nbsp;';
                        }else{
                            htmlStr += '<i class="fa fa-star-o"></i>&nbsp;';
                        }
                    }
                    htmlStr += '</span>';
                    return htmlStr;
                },
                "ordering": false
            },
            {
                data: 'nid',
                "title": "操作",
                "class":"center",
                "width":"10%",
                render:function(data,type,full,row){
                    var htmlStr = "<a class=\"btn btn-info btn-xs \" data-id=\""+data +"\" onclick=\"rule_edit('"+ data +"')\"><i class=\"fa fa-pencil\"></i> 修改 </a> ";
                    htmlStr += " <a class=\"btn btn-danger btn-xs \" data-id=\""+data +"\" onclick=\"rule_trash('"+ data +"')\"><i class=\"fa fa-trash-o\"></i> 删除 </a>";
                    return htmlStr;

                },
                "ordering": false
            }
        ],

    });

}


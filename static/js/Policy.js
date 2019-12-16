

$(document).ready( function () {
    draw_table();
} );

function draw_table() {
    $('#policy-table').DataTable({
        "serverSide": true,
        "processing": true,
        "bAutoWidth" : true,
        paging : true,
        pagingType : "simple_numbers",
        bLengthChange: false,
        ajax : function(data, callback, settings) {
            $.ajax({
                type : "GET",
                url : "/waf/api/Policy",
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
                        returnData.data = res.data.policies;
                        cluster = res.data.cluster;
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
        searching: false,
        ordering:  false,
        bInfo: false,
        columns: [
            {
                data: 'name',
                "title": "名称",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){

                    return data;
                },
            },
            {
                data: 'kind',
                "title": "类型",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    var html_str = "";
                    if (data == "base"){
                        html_str = '<li style="list-style-type:none"><button class="btn btn-xs"><i class="fa fa-tag"></i> 系统</button></li>'
                    }else {
                        html_str = '<li style="list-style-type:none"><button class="btn btn-xs"><i class="fa fa-tag"></i> 自定义</button></li>'
                    }
                    return html_str;
                },
            },
            {
                data: 'cluster',
                "title": "集群",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){
                    var html_str = '全部';
                    for (var c in cluster){
                        if (cluster[c].nid == data){
                            html_str = cluster[c].name;
                        }
                    }
                    return html_str;
                },
            },
            {
                data: 'action',
                "title": "动作",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    return data;
                },
            },
            {
                data: 'request_body_access',
                "title": "过滤请求体",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    if(data == 1){
                        return '是'
                    }else{
                        return '否'
                    }
                },
            }, 
            {
                data: 'response_body_access',
                "title": "过滤响应体",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    if(data == 1){
                        return '是'
                    }else{
                        return '否'
                    }
                },
            },                      
            {
                data: 'uuid',
                "title": "操作",
                "class":"center",
                "width":"25%",
                render: function(data,type,full,row){
                    var htmlStr = "<a class=\"btn btn-info btn-xs \" data-id=\""+data +"\" onclick=\"edit_policy('"+ data +"')\"><i class=\"fa fa-pencil\"></i> 修改 </a> ";
                    htmlStr += " <a class=\"btn btn-danger btn-xs \" data-id=\""+data +"\" onclick=\"del_policy('"+ data +"')\"><i class=\"fa fa-trash-o\"></i> 删除 </a> ";
                    return htmlStr;
                },
            }
        ],

    });
}

function edit_policy(uuid) {
    location.href = "/PolicyEdit/" + uuid;
}

function del_policy(uuid) {
    $('#del_policy_uuid').val(uuid);
    $('#del_policy_modal').modal();
}
function del_policy_confirm() {
    $.ajax({
    type: 'DELETE',
    url: '/waf/api/PolicyEdit/'+ $('#del_policy_uuid').val(),
    contentType: 'application/json',
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


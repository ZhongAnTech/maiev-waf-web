


$(document).ready( function () {
    draw_table();
} );


function draw_table() {
    $('#user-table').DataTable({
        "serverSide": true,
        "processing": true,
        "bAutoWidth" : true,
        paging : true,
        pagingType : "simple_numbers",
        bLengthChange: false,
        ajax : function(data, callback, settings) {
            $.ajax({
                type : "GET",
                url : "/waf/api/User"+document.location.search,
                cache : true, //禁用缓存
                data : {'start': data.start, 'search': data.search.value, 'size': 10, 'draw': data.draw},
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
                        returnData.data = res.data.users;
                        var cluster = res.data.cluster;
                        $(".select2_demo_2").selectize({
                            persist: false,
                            maxItems:10,
                            valueField:'nid',
                            labelField: 'name',
                            options:cluster,
                        });
                        // for (var c in cluster){
                        //     $('#web_form_cert').append('<option value="'+certs[c].nid+'">'+certs[c].name+'</option>')
                        // };
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
        columns: [
            {
                data: 'name',
                "title": "姓名",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){

                    return data;
                },
            },
            {
                data: 'username',
                "title": "用户名",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    return data
                },
            },
            {
                data: 'email',
                "title": "邮箱",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){
                    return data;
                },
            },
            {
                data: 'phone',
                "title": "手机号",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){
                    return data;
                },
            },
            {
                data: 'origin',
                "title": "来源",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    var origins = {
                        'anlink': '安链云',
                        'aegis_waf': 'WAF后台',
                        'za_sso': '众安SSO'
                    };
                    return htmlEncode(origins[data])
                },
            },
            {
                data: 'role',
                "title": "权限",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    var roles = {
                        5: '超级管理员',
                        3: '普通管理员',
                        1: '用户',
                        2: '审计员'
                    };
                    return htmlEncode(roles[data])
                },
            },
            {
                data: 'nid',
                "title": "操作",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){
                    var html_str =
                        '<button class="btn btn-xs btn-primary" onclick="edit_cert(\''+data+'\')"> 编辑 </button>&nbsp;' +
                        '<button class="btn btn-xs btn-warning" onclick="del_cert(\''+data+'\',\''+full.email+'\')"> 删除 </button>'
                    return html_str;
                },
            },
        ],

    });

}




function edit_cert(nid) {
    var data = null;
    $('#cert_form')[0].reset();
    $("#cert_clusters")[0].selectize.clear()
    if (nid){
        $.getJSON("/waf/api/User/"+nid,function(result){
            if (result['success']){
                data = result['data'];
                $('#cert_nid').val(data.nid);
                $('#cert_name').val(data.name).attr("readonly",true);
                $('#cert_email').val(data.email).attr("readonly",true);
                $('#cert_phone').val(data.phone).attr("readonly",true);
                $('#cert_origin').val(data.origin).attr("disabled","");;
                $('#cert_username').val(data.username);
                $('#cert_role').val(data.role);
                for (var a in data.clusters){
                    $("#cert_clusters")[0].selectize.addItem(data.clusters[a]);
                };
            }
            else {
                toastr.error('错误',result['info'])
            }
        });
    }else {
        $('#cert_name').removeAttr("readonly");
        $('#cert_email').removeAttr("readonly");
        $('#cert_phone').removeAttr("readonly");
        $('#cert_origin').removeAttr("disabled");
        $('#cert_edit_title').html(htmlEncode('添加用户'));
    }
    $('#edit_modal').modal();
}


function cert_sub() {
    var cert_data = $("#cert_form").serializeObject();
    cert_data.nid = $('#cert_nid').val();
    cert_data.clusters = $("#cert_clusters").val();

    var url = '/waf/api/User';
    if (cert_data.nid){
        url = '/waf/api/User/'+cert_data.nid
    }
    $.ajax({
        type: 'POST',
        url: url,
        contentType: 'application/json',
        data: JSON.stringify(cert_data),
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


function del_cert(nid,name) {
    $('#del_cert_name').html(name);
    $('#del_cert_nid').val(nid);
    $('#del_cert_modal').modal();
}

function del_cert_confirm() {
    $.ajax({
    type: 'DELETE',
    url: '/waf/api/User/'+ $('#del_cert_nid').val(),
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


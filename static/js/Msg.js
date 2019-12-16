


$(document).ready( function () {
    draw_table();
} );


function draw_table() {
    $('#cert-table').DataTable({
        "serverSide": true,
        "processing": true,
        "bAutoWidth" : true,
        paging : true,
        pagingType : "simple_numbers",
        bLengthChange: false,
        ajax : function(data, callback, settings) {
            $.ajax({
                type : "GET",
                url : "/waf/api/Msg",
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
                        returnData.data = res.data.msgs;
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
                data: 'genre',
                "title": "类型",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){

                    return data;
                },
            },
            {
                data: 'target',
                "title": "目标环境",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){

                    return data;
                },
            },
            {
                data: 'content',
                "title": "内容",
                "class":"center",
                "width":"45%",
                render: function(data,type,full,row){
                    console.log(data);
                    var html_str = '';
                    for (var d1 in data.suc){
                        html_str+= '<strong class="text-primary">'+JSON.stringify(data.suc[d1])+'</strong><br>'
                    }
                    for (var d2 in data.fail){
                        html_str+= '<strong class="text-danger">'+JSON.stringify(data.fail[d2])+'</strong><br>'
                    }
                    return html_str;

                },
            },
            {
                data: 'nid',
                "title": "状态",
                "class":"center",
                "width":"5%",
                render: function(data,type,full,row){
                    var data = '';
                    if (full.content.fail.length != 0){
                        data = '<span class="btn btn-danger btn-xs">失败</span>'
                    }else{
                        data = '<span class="btn btn-primary btn-xs">正常</span>'
                    }
                    return data;
                },
            },
            {
                data: 'time',
                "title": "时间",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){
                    var time=new Date(parseInt(data) * 1000).toLocaleString();
                    return time;
                },
            },
            {
                data: 'username',
                "title": "操作人",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    return data;
                },
            }
        ],

    });

}




function edit_cert(nid) {
    var data = null;
    $('#cert_form')[0].reset();
    if (nid){
        $.getJSON("/waf/api/Cert/"+nid,function(result){
            if (result['success']){
                data = result['data'];
                $('#cert_name').val(data.name).attr("readonly",true);
                $('#cert_nid').val(data.nid);
                $('#cert_cert').val(data.cert);
                $('#cert_keys').val(data.keys);
            }
            else {
                toastr.error('错误',result['info'])
            }
        });
    }else {
        $('#cert_name').removeAttr("readonly");
        $('#cert_edit_title').html(htmlEncode('添加证书'));
    }
    $('#edit_modal').modal();
}


function cert_sub() {
    var cert_data = $("#cert_form").serializeObject();
    cert_data.nid = $('#cert_nid').val();
    var url = '/waf/api/Cert';
    if (cert_data.nid){
        url = '/waf/api/Cert/'+cert_data.nid
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
    url: '/waf/api/Cert/'+ $('#del_cert_nid').val(),
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
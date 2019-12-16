


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
                url : "/waf/api/Cert",
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
                        returnData.data = res.data.certs;
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
                "title": "证书名",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){

                    return '<strong>'+data+'</strong>';
                },
            },
            {
                data: 'subject',
                "title": "作用域",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){

                    return data;

                },
            },
            {
                data: 'issuer',
                "title": "颁发者",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){

                    return data;
                },
            },
            {
                data: 'expire',
                "title": "有效期",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){
                    var btime=new Date(parseInt(full.start) * 1000).toLocaleDateString();
                    var time=new Date(parseInt(data) * 1000).toLocaleDateString();
                    return btime+'-'+time;
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
                        '<button class="btn btn-xs btn-warning" onclick="del_cert(\''+data+'\',\''+full.name+'\')"> 删除 </button>'
                    return html_str;
                },
            },
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
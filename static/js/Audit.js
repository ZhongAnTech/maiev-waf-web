


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
                url : "/waf/api/Audit",
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
        searching: true,
        ordering:  false,
        bInfo: false,
        columns: [
            {
                data: 'name',
                "title": "用户",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){

                    return '<strong>'+data+'</strong>';
                },
            },
            {
                data: 'subject',
                "title": "操作内容",
                "class":"center",
                "width":"50%",
                render: function(data,type,full,row){

                    return data;

                },
            },
            {
                data: 'issuer',
                "title": "时间",
                "class":"center",
                "width":"30%",
                render: function(data,type,full,row){

                    return data;
                },
            },
        ],

    });

}

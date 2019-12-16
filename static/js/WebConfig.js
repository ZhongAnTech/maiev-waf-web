
max_order = 0;
server = [];


jQuery(function($){

    // 添加服务地址
    $("#addFeild").on("click",function(){
            var column = $("#column").val();
            var weight = $("#columnType").val();
            var columnType = "weight=";
            if (weight){
                var re = /^[1-9]+[0-9]*]*$/;
                if (!re.test(Number(weight)))
                {
                    alert("权重值输入不规范！");
                    return;
                }
                columnType = columnType + weight;
            } else {
                columnType = columnType + "1";
            }
            if(column == ""){
                alert("服务地址不能为空!");
                return;
            }else{
                var isduplicate = false;
                if(!isduplicate){
                    if(/^(.*?)[a-zA-Z]/.test(column)){
                        var tag = $("<div class=\"form-group\" id=\"column_tags_num\" >" + "<label class=\"col-lg-3 control-label\"></label>" + "<div class=\"tag column-tag col-lg-9\" data-column=\""+column + "\" data-columntype=\""+columnType+"\" ><span id='address' class='address' name='address'>" + column + "</span><a  href=\"#\" class=\"close-tag\" data-original-title=\"Removing tag\">x</a></div>" + "</div>");
                    }else {
                        var tag = $("<div class=\"form-group\" id=\"column_tags_num\" >" + "<label class=\"col-lg-3 control-label\"></label>" + "<div class=\"tag column-tag col-lg-9\" data-column=\""+column + "\" data-columntype=\""+columnType+"\" ><span id='address' class='address' name='address'>" + column + "    " + columnType + "</span><a  href=\"#\" class=\"close-tag\" data-original-title=\"Removing tag\">x</a></div>" + "</div>");
                    }
                    tag.appendTo("#column_tags");
                    tag.on("click",function(){
                        $(this).remove();
                    });
                }
            }

        });

    //解决模态框背景色越来越深的问题
    $(document).on('show.bs.modal', '.modal', function(event) {
        $(this).appendTo($('body'));
    }).on('shown.bs.modal', '.modal.in', function(event) {
        setModalsAndBackdropsOrder();
    }).on('hidden.bs.modal', '.modal', function(event) {
        setModalsAndBackdropsOrder();
    });

    function setModalsAndBackdropsOrder() {
        var modalZIndex = 1040;
        $('.modal.in').each(function(index) {
            var $modal = $(this);
            modalZIndex++;
            $modal.css('zIndex', modalZIndex);
            $modal.next('.modal-backdrop.in').addClass('hidden').css('zIndex', modalZIndex - 1);
        });
        $('.modal.in:visible:last').focus().next('.modal-backdrop.in').removeClass('hidden');
    }

    //覆盖Modal.prototype的hideModal方法
    $.fn.modal.Constructor.prototype.hideModal = function () {
        var that = this
        this.$element.hide()
        this.backdrop(function () {
            //判断当前页面所有的模态框都已经隐藏了之后body移除.modal-open，即body出现滚动条。
            $('.modal.fade.in').length === 0 && that.$body.removeClass('modal-open')
            that.resetAdjustments()
            that.resetScrollbar()
            that.$element.trigger('hidden.bs.modal')
        })
    }
});

$(document).ready( function () {
    draw_table();

    $(".conf_type").click(function () {
        if ($(this).val() == 'professional'){
            $('#custom_conf').attr("hidden",true);
            $('#proxy_services').removeAttr("hidden")
        }else if ($(this).val() == 'custom'){
            $('#proxy_services').attr("hidden",true);
            $('#custom_conf').removeAttr("hidden");
        }
    });


    $("#web_form_https").click(function () {
        if ($('#https_options').val()==1){
            $('#https_options').val(0).attr("hidden",true)
        }else if ($('#https_options').val()==0){
            $('#https_options').val(1).removeAttr("hidden")
        }
    });


} );

function edit_web(nid) {
    var data = null;
    $('#web_form')[0].reset();
    if (nid){
        $.getJSON("/waf/api/WebConfig/"+nid,function(result){
            if (result['success']){
                data = result['data'];

                $('#web_form_name').val(data.name).attr("readonly",true);
                $('#web_nid').val(data.nid);


                $('#web_form_cert').val(data.cert);
                $('#web_form_mark').val(data.mark);
                $('#conf_file').val(data.conf_file);
                if (data.https == 1){
                    $('#web_form_https').attr("checked",true);
                    $('#https_options').val(1).removeAttr("hidden")
                }else{
                    $('#web_form_https').removeAttr("checked");
                    $('#https_options').val(0).attr("hidden",true)
                };

                if (data.http == 1){
                    $('#web_form_http').attr("checked",true);
                }else{
                    $('#web_form_http').removeAttr("checked");
                };

                if (data.https_trans == 1){
                    $('#web_form_https_trans').attr("checked",true);
                }else{
                    $('#web_form_https_trans').removeAttr("checked");
                };

                if (data.conf_type == "custom"){
                    $('#web_form_cus').attr("checked",true);
                    $('#web_form_pro').removeAttr("checked");

                    $('#proxy_services').attr("hidden",true);
                    $('#custom_conf').removeAttr("hidden");
                }else if (data.conf_type == "professional") {
                    $('#web_form_pro').attr("checked",true);
                    $('#web_form_cus').removeAttr("checked");
                    $('#custom_conf').attr("hidden",true);
                    $('#proxy_services').removeAttr("hidden")
                }

                server = data.server;
                edit_server(server);
            }
            else {
                toastr.error('错误',result['info'])
            }
        });
    }else {
        $('#web_form_name').removeAttr("readonly");
        $('#edit-modal-title').html(htmlEncode('添加站点'));
        server = [];
        edit_server(server);
    }
    $('#edit_modal').modal();
}

function config_web(nid,name) {
    $('#configure_form')[0].reset();
    $('#configure_name').html(name);
    $('#configure_nid').val(nid);
    if (nid){
        $.getJSON("/waf/api/WebConfig/"+nid,function(result){
            if (result['success']){
                var data = result['data'];
                var count_name = [
                    'defend_web','defend_cc',
                    'defend_blacklist','defend_custom',
                    'defend_web_policy', 'defend_cc_time',
                    'defend_cc_count', 'defend_custom_policy'];
                for (var key in count_name){
                    console.log(count_name[key]);
                    $("#"+count_name[key]).val(data[count_name[key]]);
                }
            }
            else {
                toastr.error('错误',result['info'])
            }
        });
    }
    $('#configure_modal').modal();

}

function configure_web() {

    var configure_data = $("#configure_form").serializeObject();

    var url = '/waf/api/WebConfig/'+ $('#configure_nid').val();
        $.ajax({
        type: 'PUT',
        url: url,
        contentType: 'application/json',
        data: JSON.stringify(configure_data),
        success: function (res) {
            if (res.success){
                cluster_reload();
                location.reload();
            }
            else{
                toastr.error('错误',res['info'])
            }
        },
        dataType: "json"
    });

}

function web_sub() {

    var web_data = $("#web_form").serializeObject();
    web_data.nid = $('#web_nid').val();
    web_data.cluster = $('#web-clu').val();
    var url = '/waf/api/WebConfig';
    if (web_data.nid){
        url = '/waf/api/WebConfig/'+web_data.nid
    }
    web_data.server = server;
    console.log(web_data);
    $.ajax({
        type: 'POST',
        url: url,
        contentType: 'application/json',
        data: JSON.stringify(web_data),
        success: function (res) {
            console.log(res);
            if (res.success){
                cluster_reload();
                location.reload();
            }else{
                toastr.error('错误',res['info'])
            }
        },
        dataType: "json"
    });

}

function cluster_reload() {
    var nid = $('#web-clu').val();
    var name = $('#web-clu').html();
    if (nid){
        $.getJSON("/waf/api/ClusterReload/"+nid,function(result){
            if (result['success']) {
                // 前段显示reload时间
                alert(name + `集群重启时间为： ${result['time']}`);
            }
            else {
                toastr.error('获取reload时间错误', result['info'])
            }
        });
    } else {
        toastr.error('获取不到集群nid')
    }
}

function web_edit_server(nid) {
    server_cancel();

    $('#server_form')[0].reset();

    if (nid){
        for (var s in server){
        if (server[s].nid == nid){
            $('#nid').val(server[s].nid);
            $('#status').val(server[s].status);
            $('#location_url').val(server[s].location_url);
            $('#location_pattern').val(server[s].location_pattern);
            $('#rewrite_flag').val(server[s].rewrite_flag);
            $('#rewrite_matches').val(server[s].rewrite_matches);
            $('#rewrite_pattern').val(server[s].rewrite_pattern);
            $('#slb_alg').val(server[s].slb_alg);
            $('#websocket').val(server[s].websocket);
            // $('#proxy_service').val(server[s].proxy_service);
            $('#order').val(server[s].order);

            var servers = new Array();
            servers = server[s].proxy_service;
            for (var v in servers) {
                var tag = $("<div class=\"form-group\" id=\"column_tags_num\" >" + "<label class=\"col-lg-3 control-label\"></label>" + "<div class=\"tag column-tag col-lg-9\" data-column=\""+column + "\" data-columntype=\""+columnType+"\" ><span id='address' class='address' name='address'>" + servers[v] + "</span><a  href=\"#\" class=\"close-tag\" data-original-title=\"Removing tag\">x</a></div>" + "</div>");
                tag.appendTo("#column_tags");
                tag.on("click",function(){
                    $(this).remove();
                });
            }
        }
    }
    }else {
        $('#status').val(1);
        $('#server_edit_name').html(htmlEncode('添加服务'));

    }
    $('#server_edit').modal();

}




$("input[type='radio']").click(function () {
    var ck_id=$(this).attr("id");
    var ck_val=$(this).val();
    if (ck_id == "inlineRadio1"){
        $('#custom_conf').attr("hidden",true);
        $('#proxy_services').removeAttr("hidden")
    };
    if (ck_id == "inlineRadio2"){
        $('#proxy_services').attr("hidden",true);
        $('#custom_conf').removeAttr("hidden")
    };
})


function edit_server(data) {
    var server_table = $('#server_table').dataTable();
    server_table.fnClearTable();
    server_table.fnDestroy();
    $('#server_table').empty();
    console.log(data);
    var datas = [];
    for (var s in server){
        if (server[s].status == 1){
            datas.push(server[s]);
        };
        if (server[s].order >= max_order){
            max_order = server[s].order+1;
        }
    }
    console.log(datas);
    $('#server_table').DataTable({
        data: datas,
        paging : false,
        bLengthChange: false,
        searching: false,
        "order": [[ 0, "asc" ]],
        bInfo: false,
        columns: [
            {
                data: 'order',
                visible: false,
                ordering: true,
                render:function(data, type, row){
                    return htmlEncode(data);
                },
            },
            {
                data: 'nid',
                "title": "路径匹配",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){

                    return '<li  style="list-style-type:none">模式: <span class="btn btn-default btn-xs">'+full.location_pattern+'</span></li>' +
                           '<li  style="list-style-type:none">URL: <span class="btn btn-default btn-xs">'+full.location_url+'</span></li>';
                },
            },

            {
                data: 'proxy_service',
                "title": "服务地址",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){
                    var proxy_service = '';
                    for (var a in data){
                        proxy_service += '<li  style="list-style-type:none"><span class="btn btn-default btn-xs">'+data[a]+'</span></li>'
                    };
                    return proxy_service;
                },
            },

            {
                data: 'nid',
                "title": "路径重写",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){

                     return '<li  style="list-style-type:none">Flag: <span class="btn btn-default btn-xs">'+full.rewrite_flag+'</span></li>' +
                           '<li  style="list-style-type:none">Matche: <span class="btn btn-default btn-xs">'+full.rewrite_matches+'</span></li>' +
                         '<li  style="list-style-type:none">Pattern: <span class="btn btn-default btn-xs">'+full.rewrite_pattern+'</span></li>';
                },
            },

            {
                data: 'nid',
                "title": "其他配置",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){
                    var other_status = {
                        0: "关闭",
                        1: "开启",
                    };
                    var other_sbg = {
                        0: "轮询",
                        1: "IP hash",
                        2: "session sticky"
                    };

                   return '<li  style="list-style-type:none">HTTP回源: <span class="btn btn-default btn-xs">'+other_status[full.http_back]+'</span></li>' +
                           '<li  style="list-style-type:none">Websocket: <span class="btn btn-default btn-xs">'+other_status[full.websocket]+'</span></li>' +
                       '<li  style="list-style-type:none">SLB算法: <span class="btn btn-default btn-xs">'+other_sbg[full.slb_alg]+'</span></li>';
                },
            },

            {
                data: 'nid',
                "title": "操作",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){

                     return  '<li  style="list-style-type:none"><button class="btn btn-success btn-xs" onclick="server_up(\''+data+'\',\''+full.order+'\')">上升</button>' +
                         '<button class="btn btn-xs btn-warning" onclick="server_down(\''+data+'\',\''+full.order+'\')">下降</button></li>' +
                         '<li  style="list-style-type:none"><button class="btn btn-xs btn-default" onclick="web_edit_server(\''+data+'\')">编辑</button>' +
                         '<button class="btn btn-xs btn-danger" onclick="server_del(\''+data+'\')">删除</button></li>';
                },
            }
        ]

    })

}


function del_web(nid,name) {

    $('#del_web_name').html(name);
    $('#del_web_nid').val(nid);
    $('#del_web_modal').modal();

}


function web_del_c() {
        var url = '/waf/api/WebConfig/'+ $('#del_web_nid').val();
        $.ajax({
        type: 'DELETE',
        url: url,
        contentType: 'application/json',
        success: function (res) {
            if (res.success){
                cluster_reload();
                location.reload();
            }
            else{
                toastr.error('错误',res['info'])
            }
        },
        dataType: "json"
    });

}


function add_proxy_server() {

    var html_str = '<div class="input-group">\n' +
        '<input type="text" class="form-control" name="proxy_service">\n' +
        '<span class="input-group-btn">\n' +
        '<button type="button" class="btn btn-default" onclick="$(this).parent().parent().remove()">删减</button>\n' +
        '<button type="button" class="btn btn-primary" onclick="add_proxy_server()">增加</button>\n' +
        '</span>\n' +
        '</div>';
    $('#proxy_services').append(html_str);

}


function server_cancel() {
    $("#column_tags").empty();
}


function server_sub() {

    var proxy_service = new Array();
    $("[id='address']").each(function(){
        proxy_service.push($(this).html());
    });

    var server_data = $("#server_form").serializeObject();
    if (server_data.nid){
        server_data.proxy_service = proxy_service;
        for (var s in server){
            if (server[s].nid == server_data.nid){
                console.log(s);
                server.splice(s,1,server_data);
            }
        }
    }else{
        server_data.nid = randomString(16);
        server_data.proxy_service = proxy_service;
        server_data.order = max_order;
        server.push(server_data);
    }


    edit_server(server);
    $('#server_edit').modal('hide');

}





function server_up(nid,od) {
    if (od>0) {
        var ode = Number(od) - 1;
        for (var s in server) {
            if (server[s].order == ode) {
                server[s].order = od;
            }
        }
        ;
        for (var s in server) {
            if (server[s].nid == nid) {
                server[s].order = ode;
            }
        }
        ;
        edit_server(server);
    }
}


function server_down(nid,od) {
    var ode = Number(od)+1;
    for (var s in server){
            if (server[s].order==ode){
                server[s].order = od;
            }
        };
    for (var s in server){
            if (server[s].nid==nid){
                server[s].order = ode;
            }
        };
    edit_server(server);
}

function server_del(nid) {

    for (var s in server){
            if (server[s].nid == nid){
                server[s].status = -1;
            }
        }
    edit_server(server);
}




function randomString(len) {
　　len = len || 16;
　　var $chars = 'abcdefhijkmnprstwxyz2345678';    /****默认去掉了容易混淆的字符oOLl,9gq,Vv,Uu,I1****/
　　var maxPos = $chars.length;
　　var pwd = '';
　　for (i = 0; i < len; i++) {
　　　　pwd += $chars.charAt(Math.floor(Math.random() * maxPos));
　　}
　　return pwd;
}

function draw_table() {
    $('#web-table').DataTable({
        "serverSide": true,
        "processing": true,
        "bAutoWidth" : true,
        paging : true,
        pagingType : "simple_numbers",
        bLengthChange: false,
        ajax : function(data, callback, settings) {
            $.ajax({
                type : "GET",
                url : "/waf/api/WebConfig"+document.location.search,
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
                        returnData.data = res.data.webs;
                        var certs = res.data.certs;
                        var policy = res.data.policy;
                        $('#web_form_cert').html();
                        for (var c in certs){
                            $('#web_form_cert').append('<option value="'+certs[c].nid+'">'+certs[c].name+'</option>')
                        };

                        $('#defend_custom_policy').html('');
                        $('#defend_web_policy').html('');
                        for (var p in policy){
                            if (policy[p].kind == "custom"){
                                $('#defend_custom_policy').append('<option value="'+policy[p].nid+'">'+policy[p].name+'</option>')
                            }else if(policy[p].kind == "base"){
                                $('#defend_web_policy').append('<option value="'+policy[p].nid+'">'+policy[p].name+'</option>')
                            }
                        };
                        //关闭遮罩
                        //$wrapper.spinModal(false);
                        //调用DataTables提供的callback方法，代表数据已封装完成并传回DataTables进行渲染
                        //此时的数据需确保正确无误，异常判断应在执行此回调前自行处理完毕
                        $('#web-clu').html(htmlEncode(res.data.clusters.name)).val(res.data.clusters.nid);
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
                "title": "域名",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){

                    return '<li  style="list-style-type:none"><strong>'+data+'</strong></li>';
                },
            },
            {
                data: 'cname',
                "title": "DNS解析",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){
                    var html_str = '';
                    if (full.name_host == data){
                        html_str = '<li  style="list-style-type:none"><span><i class="fa fa-circle text-navy"></i> 正常</span></li>';
                    }
                    else {
                        html_str = '<li style="list-style-type:none"><span><i class="fa fa-circle text-danger"></i> 异常</span></li>';
                        html_str += '<li style="list-style-type:none">DNS解析: '+full.name_host+'</li>'
                    };
                    html_str += '<li style="list-style-type:none">SLB: '+full.cname+'</li>';
                    return html_str;
                },
            },
            {
                data: 'nid',
                "title": "协议",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    var html_str = '';
                    if (full.http==1){html_str+='<li style="list-style-type:none"><button class="btn btn-xs btn-default"><i class="fa fa-tag"></i> HTTP</button></li>'};
                    if (full.https==1){
                        html_str+='<li style="list-style-type:none"><button class="btn btn-xs btn-default"><i class="fa fa-tag"></i> HTTPS</button></li>';
                        if (full.https_trans ==1){
                            html_str+='<li style="list-style-type:none"><button class="btn btn-xs btn-default"><i class="fa fa-tag"></i> HTTPS强转</button></li>'
                        }
                    }

                    return html_str;
                },
            },
            {
                data: 'server',
                "title": "后端服务",
                "class":"center",
                "width":"15%",
                render: function(data,type,full,row){
                    var html_str = '';
                    for (var i in data){
                        var proxy_service = data[i].proxy_service;
                        if (data[i].backup){
                           for (var j in proxy_service){
                            html_str += '<li style="list-style-type:none">'+proxy_service[j]+'</li>'
                            }
                            break;
                        } else {
                            for (var j in proxy_service){
                            html_str += '<li style="list-style-type:none">'+proxy_service[j]+'</li>'
                            }
                        }
                    };
                    return html_str;
                },
            },
            {
                data: 'nid',
                "title": "防护设置",
                "class":"center",
                "width":"20%",
                render: function(data,type,full,row){
                    var m = {
                        '1': '<span><i class="fa fa-circle text-navy"></i> 正常</span>',
                        '0': '<span><i class="fa fa-circle text-warning"></i> 监听</span>',
                        '-1': '<span><i class="fa fa-circle text-danger"></i> 停用</span>'
                    }
                    var html_str =
                        '<li style="list-style-type:none">Web应用攻击：'+m[full.defend_web]+'</li>' +
                        '<li style="list-style-type:none">CC防护模式：'+m[full.defend_cc]+'</li>' +
                        '<li style="list-style-type:none">黑名单防护服务：'+m[full.defend_blacklist]+'</li>';
                    return html_str;
                },
            },
            {
                data: 'nid',
                "title": "操作",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    var html_style = "";
                    if (full.status==1){
                        html_style = 'disabled=\"disabled\"';
                    };
                    var html_str =
                        '<li style="list-style-type:none"><button class="btn btn-xs btn-default" onclick="edit_web(\''+data+'\')"> 编辑 </button></li>' +
                        '<li style="list-style-type:none"><button class="btn btn-xs btn-default" onclick="config_web(\''+data+'\',\''+full.name+'\')"> 配置 </button></li>' +
                        '<li style="list-style-type:none"><button class="btn btn-xs btn-default" '+html_style+' onclick="del_web(\''+data+'\',\''+full.name+'\')"> 删除 </button></li>';
                    return html_str;
                },
            },
            {
                data: 'status',
                "title": "状态",
                "class":"center",
                "width":"10%",
                render: function(data,type,full,row){
                    var checked = '';
                    if (data==1){
                        checked = 'checked'
                    };
                    var html_str = '<div class="switch" onclick="web_status_change(\''+data+'\',\''+full.nid+'\',\''+full.name+'\')"><div class="onoffswitch">' +
                        '<input type="checkbox" '+checked+' class="onoffswitch-checkbox" id="sw_'+full.nid+'">' +
                        '<label class="onoffswitch-label" for="sw_'+full.nid+'">' +
                        '<span class="onoffswitch-inner"></span>' +
                        '<span class="onoffswitch-switch"></span>' +
                        '</label>' +
                        '</div>' +
                        '</div>';
                    return html_str;
                },
            },
        ],

    });

}

function web_status_change(status,nid,name) {
    if (status==1){
        $('#web_status_name').html("确认停用网站"+name);
        $('#web_status_status').val(-1);
    }else {
        $('#web_status_name').html("确认启用网站"+name);
        $('#web_status_status').val(1);
    };
    $('#web_status_nid').val(nid);
    $('#web_status_modal').modal();

}

function web_status_confirm() {
    var url = '/waf/api/WebConfig/'+ $('#web_status_nid').val();
    $.ajax({
    type: 'PUT',
    url: url,
    contentType: 'application/json',
    data: JSON.stringify({"web_status": $('#web_status_status').val()}),
    success: function (res) {
        if (res.success){
            cluster_reload();
            location.reload();
        }
        else{
            toastr.error('错误',res['info'])
        }
    },
    dataType: "json"
});
}
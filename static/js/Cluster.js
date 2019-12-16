


$(document).ready( function () {

} );

function clu_add(nid) {
    var data = null;
    $('#clu_form')[0].reset();
    if (nid){
        $('#clu_edit_title').html(htmlEncode('配置集群'));
        $.getJSON("/waf/api/Cluster/"+nid,function(result){
            if (result['success']){
                data = result['data'];
                $('#clu_name').val(data.name).attr("readonly",true);
                $("#clu_eshost").val(data['eshost']);
                $("#clu_ngxhost").val(data['ngxhost']);
                for (var a in data){
                    console.log(data[a]);
                    $("#clu_form").find("input[name='"+ a +"']").val(data[a]);
                };
            }
            else {
                toastr.error('错误',result['info'])
            }
        });
    }else {
        $('#clu_name').removeAttr("readonly");
        $('#clu_edit_title').html(htmlEncode('添加集群'));
    }
    $('#edit_modal').modal();

}

function clu_sub() {
    var clu_data = $("#clu_form").serializeObject();
    clu_data.nid = $('#clu_nid').val();
    var url = '/waf/api/Cluster';
    if (clu_data.nid){
        url = '/waf/api/Cluster/'+clu_data.nid
    }
    $.ajax({
        type: 'POST',
        url: url,
        contentType: 'application/json',
        data: JSON.stringify(clu_data),
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


function clu_stop(nid) {
        var url = '/waf/api/Cluster/'+nid
        $.ajax({
        type: 'DELETE',
        url: url,
        contentType: 'application/json',
        success: function (res) {
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


function clu_del() {
        var url = '/waf/api/Cluster/'+ $('#del_clu_nid').val();
        $.ajax({
        type: 'DELETE',
        url: url,
        contentType: 'application/json',
        success: function (res) {
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


function clu_del_c(nid,name) {
    $('#del_clu_name').html(name);
    $('#del_clu_nid').val(nid);
    $('#del_clu_modal').modal();
}


function clu_reload_c(nid,name) {
    $('#reload_clu_name').html(name);
    $('#reload_clu_nid').val(nid);
    $('#reload_clu_modal').modal();
}


function clu_reload() {
        var url = '/waf/api/Cluster/'+ $('#reload_clu_nid').val();
        $.ajax({
        type: 'PUT',
        url: url,
        contentType: 'application/json',
        success: function (res) {
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
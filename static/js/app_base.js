jQuery.prototype.serializeObject=function(){
    var a,o,h,i,e;
    a=this.serializeArray();
    o={};
    h=o.hasOwnProperty;
    for(i=0;i<a.length;i++){
        e=a[i];
        if(!h.call(o,e.name)){
            o[e.name]=e.value;
        }
    }
    return o;
};

function htmlEncode(str) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
function htmlDecode(str) {
    var div = document.createElement("div");
    div.innerHTML = str;
    return div.innerText;
}

function guid() {
  function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
  }
  return s4()+s4();
}

function AppPage(){

}
AppPage.prototype = {
    postData:function(url,data,success,failed){
        $.ajax({
            url:url,
            dataType:"json",
            type:"post",
            contentType: 'application/json',
            data:JSON.stringify(data),
            success:function(result){
                if(result.success){
                    return success(result);
                }else{
                    toastr.error('错误',result.reason)
                    return failed(result);
                }
            },
            error:function(result){
                toastr.error('错误','后端服务异常')
                return failed(result);
            }

        });
    },
    getData:function(url,callback,failed){
        $.ajax({
            url:url,
            dataType:"json",
            type:"get",
            contentType: 'application/json',
            success:function(result){
                if(result.success){
                    return callback(result);
                }else{
                    toastr.error('错误',result.reason)
                    return failed(result);
                }
            },
            error:function(result){
                toastr.error('错误','后端服务异常')
                return failed(result);
            }

        });
    }

};


$(document).ready(function() {

    var path = document.location.pathname;
    if(path == '/WebConfig'){path+=document.location.search};
    if(path.indexOf('/Rules/')==0){path = '/Rules'};
    $("#side-menu").find("a[href='"+ path +"']").parents("li").addClass("active");
    $("#side-menu").find("a[href='"+ path +"']").parents("ul").addClass("in");

});
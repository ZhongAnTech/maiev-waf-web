
$(document).ready( function () {
     $("#login-btn").on("click",function(){

        var username = document.forms["form-t"]["username"].value;
        var password = document.forms["form-t"]["password"].value;
        $.ajax({
        type: 'POST',
        url: '/Login',
        contentType: 'application/json',
        data: JSON.stringify({"username": username, "password": password}),
        dataType : "json",
        success: function (res) {
            if (res.success){
                window.location.href=res.msg;
            }
            else{
                alert(res.msg);
                // toastr.error('错误',res['info'])
            }
        },
    });
});




} );

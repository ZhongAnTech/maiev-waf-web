





$(document).ready( function () {

    viewdata($('#action_btn').val());

     $(".a-clu").on("click",function(){

         var nid = $(this).attr("value");
         var name = $(this).html();
         $('#action_btn').val(nid);
         $('#clu-name').html(name);
         viewdata(nid);
         $('#view-btn').addClass("active","");
         $('#attack-btn').removeClass("active");
    });

     $("#view-btn").on("click",function(){
         $('#view-btn').addClass("active","");
         $('#attack-btn').removeClass("active");
         viewdata($("#action_btn").val());


    });

     $("#attack-btn").on("click",function(){
         $('#view-btn').removeClass("active");
         $('#attack-btn').addClass("active","");
         attack($("#action_btn").val());

    });

} );

function attack(clu) {
    $("#mode_load").mLoading();

    $.ajax({
        type: 'GET',
        url: '/waf/api/Statis?kind=attack&cluster='+clu,
        contentType: 'application/json',
        success: function (res) {
            if (res.success){
                $("#mode_load").mLoading("hide");
                draw_line(res.data.views,[1]);
                // draw_topip(res.data.top_ip);
                // draw_piep(res.data.top_ua, 'pie_1', 'pie', false);
                draw_piep(res.data.top_attack_type, 'pie_2', 'doughnut', true);
                $('#status-top').html('TOP 5 Attack');
                // draw_piep(res.data.top_web, 'pie_3', 'pie', true);


            }
            else{
                toastr.error('错误',res['info'])
            }
        },
        dataType: "json"
    });
    
}


function viewdata(clu) {
    $("#mode_load").mLoading();

    $.ajax({
        type: 'GET',
        url: '/waf/api/Statis?kind=access&cluster='+clu,
        contentType: 'application/json',
        success: function (res) {
            if (res.success){
                $("#mode_load").mLoading("hide");
                draw_line(res.data.views,[0]);
                draw_topip(res.data.top_ip);
                draw_piep(res.data.top_ua, 'pie_1', 'pie', false);
                draw_piep(res.data.top_status, 'pie_2', 'doughnut', true);
                $('#status-top').html('TOP 5 Status');
                draw_piep(res.data.top_web, 'pie_3', 'pie', true);


            }
            else{
                toastr.error('错误',res['info'])
            }
        },
        dataType: "json"
    });
}



function draw_topip(data) {
    var a = 0;
    for (var dd in data){a +=data[dd].value};
    $('#top_ips').html('');
    var d_lan = 5;
    console.log(data.length);
    if (data.length<=5){
        d_lan=data.length
    };
    for (var d=0; d<d_lan; d++){
        var p = data[d].value/a;
        var html_li = '<li>\n' +
            '                                <h4 class="no-margins">'+data[d].city+'</h4>\n' +
            '                                <small>'+data[d].name+'</small>\n' +
            '                                <div class="stat-percent">'+data[d].value+'<i class="fa fa-level-up text-navy"></i></div>\n' +
            '                                <div class="progress progress-mini">\n' +
            '                                    <div style=\"width: '+p.toPercent()+'\;\" class="progress-bar"></div>\n' +
            '                                </div>\n' +
            '                            </li>'
        $('#top_ips').append(html_li);
    }

}

Number.prototype.toPercent = function(){
return (Math.round(this * 10000)/100).toFixed(2) + '%';
}



function draw_line(data,title) {
    var labels_data = [];
    var view_data = [];
    for (var d in data){
        labels_data.push(new Date(parseInt(data[d].key) * 1000).toLocaleTimeString());
        view_data.push(data[d].doc_count);
    };
    var dataset =  [

            [{
                label: "访问量",
                backgroundColor: 'rgba(26,179,148,0.5)',
                borderColor: "rgba(26,179,148,0.7)",
                pointBackgroundColor: "rgba(26,179,148,1)",
                pointBorderColor: "#fff",
                data: view_data
            }],[{
                label: "攻击量",
                backgroundColor: 'rgba(220, 220, 220, 0.5)',
                pointBorderColor: "#fff",
                data: view_data
            }]
        ]

    var lineData = {
        labels: labels_data,
        datasets: dataset[title]
    };

    var lineOptions = {
        responsive: true
    };


    var ctx = document.getElementById("lineChart").getContext("2d");
    new Chart(ctx, {type: 'line', data: lineData, options:lineOptions});



};







function draw_piep(datas, obj_id, type, show_leg) {

    var labels_data = [];
    var count_data = [];
    var d_lan = 5;
    if (datas) {
        if (datas.length <= 5) {
            d_lan = datas.length
        };
        for (var d = 0; d < d_lan; d++) {
            labels_data.push(datas[d].key);
            count_data.push(datas[d].doc_count);
        };
    }else {
        labels_data = ['a'];
        count_data = [1]
    }


        var piep_data = {
            labels: labels_data,
            datasets: [{
                data: count_data,
                backgroundColor: ["#a3e1d4", "#dedede", "#b5b8cf", "#d3d3d3", "#bababa"]
            }]
        };


        var piepOptions = {
            responsive: true,
            legend: {
                "display": show_leg,
                "position": 'bottom',
                "fullWidth": true,
                labels: {
                    boxWidth: 10,
                    fontSize: 10
                }
            },
            tooltips: {
                "footerFontSize": 1
            }
        };


        var ctx4 = document.getElementById(obj_id).getContext("2d");
        new Chart(ctx4, {type: type, data: piep_data, options: piepOptions});

}
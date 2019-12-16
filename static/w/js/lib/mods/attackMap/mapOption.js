define(function(){

    // 颜色配置
    var COLOR_BG = 'rgba(0,0,0,0)';
    var COLOR_BORDER = 'rgba(100,149,237,1)';
    var COLOR_AREA = 'rgba(45,45,90,0.5)';
    var COLOR_AREA_HOVER = 'rgba(240,255,240,0.4)';
    var COLOR_TEXT = '#fff';
    var COLOR_LINE_EFFECT = '#fff';
    var COLOR_MARK_LINE = 'rgba(255,255,255,0.04)';
    var COLOR_MARK_POINT = 'rgba(255,0,0,0.8)';

    return {
        backgroundColor: COLOR_BG,
        color: ['gold','aqua','lime'],
        tooltip: {
            trigger: 'item',
            formatter: function(params, ticket, callback){
                // 有点矬 没法阻止
                var str = params.name;
                return (str.indexOf('>') === -1) ? str : '';
            }
        },
        series: [
            {
                name: 'map',
                type: 'map',
                mapType: 'world',
                roam: 'scale',
                scaleLimit: {
                    max: 1.5,
                    min: 1
                },
                itemStyle: {
                    normal: {
                        borderColor: COLOR_BORDER,
                        borderWidth: 0.5,
                        areaStyle: {
                            color: COLOR_AREA
                        },
                        label: {
                            show: false,
                            position: 'inside',
                            textStyle: {
                                color: COLOR_TEXT
                            }
                        }
                    },
                    emphasis: {
                        color: COLOR_AREA_HOVER
                    }
                },
                data: [],
                markLine : {
                    clickable: false,
                    symbol: ['triangle', 'none'],
                    symbolSize: [5, 4],
                    smooth: false,
                    effect: {
                        show: true,
                        scaleSize: 1,
                        period: 15,
                        color: COLOR_LINE_EFFECT,
                        shadowBlur: 20
                    },
                    itemStyle: {
                        normal: {
                            borderWidth: 1,
                            lineStyle: {
                                color: COLOR_MARK_LINE,
                                type: 'dashed',
                                width: 2,
                                shadowBlur: 5
                            }
                        }
                    },
                    data: []
                },
                markPoint : {
                    clickable: true,
                    symbol: 'emptyCircle',
                    symbolSize: function (v){
                        return 12 + v/10;
                    },
                    effect: {
                        show: true,
                        period: 30,
                        scaleSize: 2,
                        color: COLOR_MARK_POINT,
                        shadowBlur: 2
                    },
                    itemStyle: {
                        normal: {
                            label: {show:false}
                        }
                    },
                    data: []
                }
            }
        ]
    };
});
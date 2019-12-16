define(function(require){

    var U = require('underscore');
    var Util = require('mods/util');

    var EC = require('echarts/echarts');
    var ecMap = require('echarts/chart/map');
    var ecMapParams = require('echarts/util/mapData/params').params;

    var EVENT = require('echarts/config').EVENT;
    var MAP_TYPE_WORLD = 'world';
    var MAP_TYPE_CHINA = 'china';


    var AttackMap = function(config){
        this.config = U.extend({
            offset: {
                top: 0,
                bottom: 0
            },
            view: MAP_TYPE_WORLD
        }, config);

        this.el = document.getElementById(this.config.id);
        // 铺满屏幕
        this._fullscreen();
        // 初始化echarts
        this._init();
    };

    // 对外事件
    AttackMap.EVENTS = {
        VIEW_CHANGED: 'viewChanged',
        LINE_HOVERED: 'marklineHovered',
        LINE_BLURED: 'marklineBlured'
    };

    // 不带下划线的为对外暴露的方法
    AttackMap.prototype = {
        _init: function(){
            // _chart对象私有
            this._chart = EC.init(this.el);
            // default view
            var mapOption = U.extend({}, require('mods/attackMap/mapOption'));
            // 合并option
            U.extend(mapOption.series[0], this._getViewOption(this.config.view));
            // render
            this._chart.setOption(mapOption);

            // geo pos引用
            this.getPosByGeo = this._chart.chart.map.getPosByGeo;
            this.getGeoByPos = this._chart.chart.map.getGeoByPos;

            // 交互
            this._bindEvents();
        },

        _bindEvents: function(){
            var that = this;
            this._chart.on(EVENT.CLICK, function(e, chart){
                // 仅对中国钻取
                if(e.data.name === '中国' || e.data.name === 'China'){
                    that.setView(MAP_TYPE_CHINA);
                }
                // and中国省份钻取
                else if(e.data.name in ecMapParams){
                    that.setView(e.data.name);
                }
            });

            this._chart.on(EVENT.HOVER, function(e, chart){
                // 是markline
                if(e.name.indexOf('>') !== -1){
                    // 阻止此时的tooltip
                    that._chart.chart.map.component.tooltip.hideTip();
                    // FUCK无效

                    // 由外部去渲染
                    that.fire(
                        AttackMap.EVENTS.LINE_HOVERED,
                        { name: e.name },
                        e.event
                    );
                }
                // 不是markline，告诉外部
                else{
                    // 效率有点低 每次hover都会触发
                    that.fire(AttackMap.EVENTS.LINE_BLURED);
                }
            });
        },

        // 铺满屏幕
        _fullscreen: function(){
            var offset = (this.config.offset.top || 0) + (this.config.offset.bottom || 0);
            this.el.style.height = (window.innerHeight - offset) + 'px';
        },

        // view涉及到的series里需要设置的属性
        _getViewOption: function(viewType){
            if(viewType === MAP_TYPE_WORLD){
                return {
                    mapType: MAP_TYPE_WORLD,
                    nameMap: require('geo/world/countryName')
                }
            }
            else if(viewType === MAP_TYPE_CHINA){
                return {
                    mapType: MAP_TYPE_CHINA
                    // ,geoCoord: require('geo/china/city').sample  //不全
                };
            }
            else if(viewType in ecMapParams){
                return {
                    mapType: viewType
                };
            }
            return {};
        },

        _setOtherOption: function(viewType){
            if(viewType === MAP_TYPE_WORLD){
                this._chart.chart.map.series[0].itemStyle.normal.label.show = false;
                this._chart.chart.map.series[0].markLine.effect.period = 15;
            }
            else if(viewType === MAP_TYPE_CHINA){
                this._chart.chart.map.series[0].itemStyle.normal.label.show = false;
                this._chart.chart.map.series[0].markLine.effect.period = 8;
            }
            else{
                this._chart.chart.map.series[0].itemStyle.normal.label.show = true;
                this._chart.chart.map.series[0].markLine.effect.period = 4;
            }
        },

        // 设置地图视图
        setView: function(viewType){
            // 上一次的view
            (typeof this._lastView === 'undefined') && (this._lastView = this.config.view);
            // 防止重复set
            if(viewType === this._lastView){
                return false;
            }
            this._lastView = viewType;

            // 历史开过的view（string逗号分隔）
            (typeof this._historyViews === 'undefined') && (this._historyViews = this.config.view);
            // 用来判断是否加载过
            if(this._historyViews.indexOf(viewType) === -1){
                this._historyViews += (',' + viewType);
                // loading
                this._chart.showLoading();
                // 假loading
                var that = this;
                setTimeout(function(){
                    that._chart.hideLoading();
                }, 350);
            }

            // 要先reset再draw
            this.reset();
            var viewOption = this._getViewOption(viewType);
            this._chart.setSeries([viewOption]);
            // 多级的option没法merge原来的，所以得手动设置
            this._setOtherOption(viewType);
            
            // 对外fire事件
            this.fire(
                AttackMap.EVENTS.VIEW_CHANGED, 
                { viewType: viewType }
            );
        },

        // 攻击线
        setAttacks: function(data, isLoop){
            // 是否循环显示markline（暂未用到）
            isLoop = isLoop || true;
            // 留个data备份（暂未用到）
            this._mData = data;

            // TODO: 要对IP聚合
            // 国内最小定位到市级，国外只能定位到国家
            // 而markline只能通过 name-name 来标识
            // 聚合后相同 name-name 的攻击累计次数视为强度

            var lineData = U.map(data, function(v){
                return [
                    {name: v['srcName'], geoCoord: [v['srcLocX'], v['srcLocY']]},
                    {name: v['destName'], geoCoord: [v['destLocX'], v['destLocY']]}
                ]
            });

            var pointData = U.map(data, function(v){
                return {
                    name: v['destName'],
                    geoCoord: [v['destLocX'], v['destLocY']]
                }
            });

            // ECharts内部的核心变量
            var _map = this._chart.chart.map;
            // 防止addMarkLine抛异常 seriesIndex 0
            // _map.buildMark(0);

            // FUCK
            try{
                this._chart.addMarkLine(0, {data: lineData});
            }catch(e){
                // console.error(e);
            }
            
            try{
                this._chart.addMarkPoint(0, {data: pointData});
            }catch(e){
                // console.error(e);
            }
        },

        // 支持事件类型见 AttackMap.EVENTS
        on: function(type, fn){
            (typeof this._handlers === 'undefined') && (this._handlers = {});
            (typeof this._handlers[type] === 'undefined') && (this._handlers[type] = []);
            this._handlers[type].push(fn);
        },
        fire: function(type, data, event){
            if(typeof this._handlers === 'undefined' || 
                typeof this._handlers[type] === 'undefined'){
                return false;
            }

            var that = this;
            var eventObj = {
                type: type,
                data: data
            };
            // 原生event对象
            (typeof event !== 'undefined') && (eventObj.event = event);
            
            U.each(this._handlers[type], function(fn){
                fn(eventObj, that);
            });
        },
        
        // 通用方法
        refresh: function(){
            this._chart.refresh();
        },
        reset: function(){
            this._chart.restore();
        },
        resize: function(){
            this._fullscreen();
            this._chart.resize();
        }
    };

    return AttackMap;
});
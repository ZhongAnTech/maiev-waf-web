define(['jquery'], function($){

    var WEEK_NAMES = ["星期日","星期一","星期二","星期三","星期四","星期五","星期六"];
    var YEAR = '年';
    var MONTH = '月';
    var DAY = '日';
    var HOUR = ':';
    var MINUTE = ':';
    var SECOND = '';

    var formatDigit = function(d){
        return (d < 10) ? ('0'+d) : (''+d);
    };


    var Clock = function(config){
        this.config = $.extend({

        }, config);

        this.$el = $('#' + this.config.id);
        this._init();
    };

    Clock.prototype = {
        _init: function(){
            this.$el.append(
                '<div class="date">' + 
                    '<span class="yy"></span>' + 
                    '<span class="yy-unit">' + YEAR + '</span>' + 
                    '<span class="MM"></span>' + 
                    '<span class="MM-unit">' + MONTH + '</span>' + 
                    '<span class="dd"></span>' + 
                    '<span class="dd-unit">' + DAY + '</span>' + 
                    '<span class="week"></span>' + 
                '</div>' + 
                '<div class="time">' + 
                    '<span class="hh"></span>' + 
                    '<span class="hh-unit">' + HOUR + '</span>' + 
                    '<span class="mm"></span>' + 
                    '<span class="mm-unit">' + MINUTE + '</span>' + 
                    '<span class="ss"></span>' + 
                    '<span class="ss-unit">' + SECOND + '</span>' + 
                '</div>'
            );
            this.start();
        },
        _update: function(){
            var now = new Date();
            var yy = now.getFullYear();
            var MM = formatDigit(now.getMonth()+1);
            var dd = formatDigit(now.getDate());
            var hh = formatDigit(now.getHours());
            var mm = formatDigit(now.getMinutes());
            var ss = formatDigit(now.getSeconds());
            var week = WEEK_NAMES[now.getDay()];

            // 优化 减少渲染
            (yy !== this._yy) && (this._yy = yy) && this.$el.find('.yy').text(yy);
            (MM !== this._MM) && (this._MM = MM) && this.$el.find('.MM').text(MM);
            (dd !== this._dd) && (this._dd = dd) && this.$el.find('.dd').text(dd) && this.$el.find('.week').text(week);
            (hh !== this._hh) && (this._hh = hh) && this.$el.find('.hh').text(hh);
            (mm !== this._mm) && (this._mm = mm) && this.$el.find('.mm').text(mm);
            this.$el.find('.ss').text(ss);
        },
        start: function(){
            // 先初始化时间
            this._update();

            var that = this;
            this.timer = setInterval(function(){
                that._update();
            }, 1000);
        },
        stop: function(){
            clearInterval(this.timer);
            this.timer = null;
        }
    };

    return Clock;
});
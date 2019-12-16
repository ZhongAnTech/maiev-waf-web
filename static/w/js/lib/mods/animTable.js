define(['jquery', 'mods/util'], function($, Util){

    var AnimTable = function(config){
        this.config = $.extend({
            speed: 3000
        }, config);

        this.$el = $('#' + this.config.id);
        this._init();
    };

    AnimTable.prototype = {
        _init: function(){
            // 仅当table高度大于父容器时才初始化
            if(this.$el.height() > this.$el.parent().height()){
                this._preprocess();
                // run
                this.start();
            }
            else{
                // 失败标记
                this._disable = true;
            }
        },
        _preprocess: function(){
            var $table = this.$el;

            // 第一层wrapper，用来overflow和sticky
            $table.wrap('<div style="height: 100%; overflow: hidden; position: relative;"></div>');

            // 处理thead
            var $thead = $table.find('thead');
            var thHeight = $thead.height();
            // 添加sticky table
            var $sticky = $('<table class="' + $table.attr('class') + '" style="position: absolute; top: 0;"></table>');
            $sticky.append($thead.clone());
            $table.parent().append($sticky);

            // 原始thead隐藏
            $thead.css('visibility', 'hidden');
            // 原始table第二层wrapper
            $table.wrap('<div style="overflow: hidden; margin-top:' + thHeight + 'px;"></div>');
            $table.css('margin-top', -thHeight + 'px');

            // FUCK: 不知为啥真实宽度无法撑满table
            // thead与sticky定宽
            $thead.find('th').each(function(i){
                $(this).css('width', $sticky.find('th').eq(i).width() + 'px');
            });
        },
        start: function(){
            if(this._disable){
                return;
            }

            var $tbody = this.$el.find('tbody');
            var table = this.$el.get(0);
            var that = this;

            this.timer = setInterval(function(){
                var $first = $tbody.children().first();
                var h = $first.get(0).offsetHeight;

                Util.moveAnim(table, 0, 0, 0, -h, {
                    isClear: true,
                    afterAnim: function(){
                        $tbody.append($first);
                    }
                });

            }, this.config.speed);
        },
        stop: function(){
            if(this._disable){
                return;
            }
            
            clearInterval(this.timer);
            this.timer = null;
        }
    };

    return AnimTable;
});
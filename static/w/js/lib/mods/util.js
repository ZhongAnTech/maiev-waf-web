define(['jquery', 'underscore'], function($, U){
    return {
        /* 移动动画
            @param el {HTMLElement}
            @param x1 {number}
            @param y1 {number}
            @param x2 {number}
            @param y2 {number}
            @param config {Object}
                @param duration {number}
                @param ease {string}
                @param isShowEl {boolean} 动画结束后是否继续显示元素
                @param isClear {boolean} 动画结束后是否清除动画属性
                @param beforeAnim {Function}
                @param afterAnim {Function}
        */
        moveAnim: function(el, x1, y1, x2, y2, config) {
            if(!el){
                return;
            }
            if(!el.tagName && el.length){
                // jquery节点
                el = el[0];
            }

            var style = el.style;
            config = U.extend({
                duration: 400,
                ease: 'ease',
                isShowEl: true,
                isClear: false
            }, config);

            style.display = 'block';
            style.transform = 'translate3d(' + x1 + 'px, ' + y1 + 'px, 0px)';
            style.transitionDuration = '0ms';
            style.webkitTransform = 'translate3d(' + x1 + 'px, ' + y1 + 'px, 0px)';
            style.webkitTransitionDuration = '0ms';

            // before animation
            config.beforeAnim && config.beforeAnim();

            setTimeout(function() {
                style.transform = 'translate3d(' + x2 + 'px, ' + y2 + 'px, 0px)';
                style.transitionDuration = config.duration + 'ms';
                style.transitionTimingFunction = config.ease;
                style.webkitTransform = 'translate3d(' + x2 + 'px, ' + y2 + 'px, 0px)';
                style.webkitTransitionDuration = config.duration + 'ms';
                style.webkitTransitionTimingFunction = config.ease;

                // 下面不会有第二次setTimeout
                if(config.isShowEl && !config.isClear){
                    // after animation
                    config.afterAnim && config.afterAnim();
                }
            }, 0);

            // 动画结束后不显示元素
            if(!config.isShowEl){
                style.display = 'none';
            }
            // 清空动画属性（下次show时显示在最初的位置）
            if(!config.isShowEl || config.isClear){
                var that = this;
                setTimeout(function() {
                    that._clearTransform(el);
                    // after animation
                    config.afterAnim && config.afterAnim();
                }, config.duration + 10);
            }
        },

        _clearTransform: function(el){
            var style = el.style;
            style.transform = null;
            style.transitionDuration = null;
            style.transitionTimingFunction = null;
            style.webkitTransform = null;
            style.webkitTransitionDuration = null;
            style.webkitTransitionTimingFunction = null;
        }
    }
});
require([
    'jquery',
    'mods/clock',
    'mods/attackMap/main',
    'mods/util',
    'mods/animTable',
    'mods/attackMap/mock'

], function($, Clock, AttackMap, Util, AnimTable, Mock){

    // 别名
    var MAP_EVENTS = AttackMap.EVENTS;

    // main
    var View = {
        // 作为一个视图模版来初始化
        init: function(){
            // 此View片段的root元素
            // this.$el = $('body');

            // 初始化成员
            this.clock = new Clock({
                id: 'timeClock'
            });

            this.aMap = new AttackMap({
                id: 'mapChart',
                offset: {
                    top: $('#mapChart').offset().top
                },
                view: 'world'  //TODO根据单位
            });

            this.sitesTableAnim = new AnimTable({
                id: 'sitesTable'
            });

            // 绑定事件
            this._bindEvents();
        },

        _bindEvents: function(){
            var that = this;

            // 视图切换
            this._bindMapViewEvents();
            // 攻击线显示详情
            this._bindMapLineEvents();
            // 监控表格动画
            this._bindMonitorEvents();

            // 其他binding
            $(window).on('resize', function(){
                that.aMap.resize();
            });
        },

        // 视图切换事件
        _bindMapViewEvents: function(){
            var that = this;

            // AttackMap监听
            this.aMap.on(MAP_EVENTS.VIEW_CHANGED, function(e){
                var type = e.data.viewType;
                // 清空当前
                $current = $('.view-nav.active');
                $current.removeClass('active');

                // 目标
                var $target = $('.view-nav[data-type="' + type + '"]');
                if($target.length == 0){
                    // 另起一个
                    var $copy = $current.clone();
                    $copy.addClass('active').attr('data-type', type).text(type);
                    $('#dynamicNav').empty().append($copy);
                }
                else{
                    $target.addClass('active');
                }
            });

            // NOTE: 会有动态生成的元素
            $('.J_changeView').live('click', function(){
                that.aMap.setView($(this).attr('data-type'));
            });
        },

        // 攻击线(地图markline)事件
        _bindMapLineEvents: function(){
            var that = this;

            this.aMap.on(MAP_EVENTS.LINE_HOVERED, function(e){
                // 前提：srcName-destName 必须能唯一区分
                // 国外IP目前只能定位到国家
                var temps = (e.data.name).split(' > ');
                var source = temps[0];
                var dest = temps[1];

                var attacks = that.attacksData;
                // 遍历data
                for(var i=0; i<attacks.length; i++){
                    if(attacks[i]['srcName'] === source && attacks[i]['destName'] === dest){
                        that._drawMapLineDetail(attacks[i], e.event.pageX, e.event.pageY);
                        break;
                    }
                }
            });

            this.aMap.on(MAP_EVENTS.LINE_BLURED, function(e){
                that._hideMapLineDetail();
            });
        },

        // 监控表格事件
        _bindMonitorEvents: function(){
            var that = this;

            $('.J_changeMonitor').bind('click', function(){
                var el = $(this).closest('.monitor').get(0);
                var status = $(this).attr('data-status');
                var orient = $(this).attr('data-orient');  //暂时只有bottom和right

                if(status !== 'hide'){
                    (orient === 'bottom') ? 
                        Util.moveAnim(el, 0, 0, 0, el.offsetHeight)
                        : Util.moveAnim(el, 0, 0, el.offsetWidth, 0);
                    $(this).attr('data-status', 'hide').text('展开');
                }
                else{
                    (orient === 'bottom') ? 
                        Util.moveAnim(el, 0, el.offsetHeight, 0, 0)
                        : Util.moveAnim(el, el.offsetWidth, 0, 0, 0);
                    $(this).attr('data-status', '').text('收起');
                }
            });
        },

        // 画攻击线详情
        _drawMapLineDetail: function(attack, posX, posY){
            // 前提：source-dest 只能存在一条攻击线（多次攻击的话累计强度）
            var id = 'attack_' + attack['srcName'] + '_' + attack['destName'];
            var $frag = $('#' + id);

            if($frag.length === 0){
                $frag = $('<div id="' + id + '" class="attack-detail"></div>');
                $frag.append(
                    '<p>时间: ' + attack['time'] + '</p>' + 
                    '<p>类型: ' + attack['type'] + '攻击' + '</p>' + 
                    '<p>攻击源: ' + attack['srcIp'] + ' (' + attack['srcName'] + ')' + 
                    '<p>攻击目标: ' + attack['destIp'] + ' (' + attack['destName'] + ')'
                );

                // this.$el
                $('body').append($frag);
            }

            // 定位（做了修正，tooltip的默认点位置）
            $frag.css({
                position: 'fixed',
                top: (posY-15) + 'px',
                left: (posX+20) + 'px'
            });

            // 显示标记
            $frag.addClass('current').show();

            // 隐藏同行
            $frag.siblings('.attack-detail.current')
                .removeClass('current').hide();
        },

        _hideMapLineDetail: function(){
            $('.attack-detail.current').removeClass('current').hide();
        },

        // 攻击数据展现
        _renderAttacks: function(data){
            // render map
            this.aMap.setAttacks(data);

            // render table
            var $tbody = $('#attacksTable').find('tbody');
            // var $frags = [];
            // $('#data_tbody').html('');
            $.each(data, function(i, v){
                var $tr = $('<tr><td>'+v['srcIp']+'</td><td>'+v['srcName']+'</td><td>'+v['destIp']+'</td><td>'+v['destName']+'</td><td>'+v['type']+'</td><td>'+v['time']+'</td></tr>');
                $tbody.append($tr);
            });

            View.init里的延迟成员
            this.attacksTableAnim = new AnimTable({
                id: 'attacksTable'
            });
        },

        // 获取攻击数据
        getAttacks: function(){
            var that = this;
            $.post(
                '/waf/api/AttackGraph',
                '{"type":"get"}',
                function(data){
                    console.log(data.data);
                    that._renderAttacks(data.data);
                }
            );

            // 本地mock数据
            /*
            that.attacksData = Mock.data;
            that._renderAttacks(that.attacksData);
            console.log(that.attacksData);
            */
        }
    };

    // execution
    View.init();

    // lazy load
    setTimeout(function(){
        View.getAttacks();
    }, 16);

    setTimeout(function(){
        $('#sitesDiv').find('.J_changeMonitor').click();
    }, 3000);

    setInterval(function(){
        View.getAttacks();
    }, 10000);

});


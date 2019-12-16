define([
    'zrender/shape/line',
    'zrender/shape/circle',
    'zrender/animation/animation'
], function(){

    return {
        test: function(zr){
            var shapeId = '123456';

            zr.addShape(
                new LineShape({
                    id: shapeId,
                    // z: 3,
                    zlevel: 1,
                    style: {
                        xStart : 100,
                        yStart : 100,
                        xEnd : 200,
                        yEnd : 100,
                        strokeColor : 'rgba(135, 206, 250, 0.8)',
                        lineWidth : 3,
                        lineType : 'solid'
                    }
                })
            );

            zr.animate(shapeId, 'style', true)
                .when(1000, {
                    xStart : 500,
                    yStart : 100,
                    xEnd : 600,
                    yEnd : 100
                })
                .start();

            zr.render();
        }
    }
});
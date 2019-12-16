requirejs.config({
    baseUrl: '/static/w/js/lib',
    paths: {
    	jquery: '/static/w/js/jquery.min',
        underscore: '/static/w/js/underscore-min'
    },
    packages: [
        {
            name: 'echarts',
            location: 'echarts/src',
            main: 'echarts'
        },
        {
            name: 'zrender',
            location: 'zrender/src',
            main: 'zrender'
        }
    ]
});
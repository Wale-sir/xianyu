// 通用函数
function showLoading(element) {
    element.innerHTML = '<div class="loading"></div>';
}

function hideLoading(element) {
    element.innerHTML = '';
}

function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
}

// 图表相关函数
function createCandlestickChart(data, container) {
    const trace = {
        x: data.dates,
        open: data.open,
        high: data.high,
        low: data.low,
        close: data.close,
        type: 'candlestick',
        name: 'K线图'
    };

    const layout = {
        title: '股票K线图',
        yaxis: {
            title: '价格'
        },
        xaxis: {
            title: '日期'
        }
    };

    Plotly.newPlot(container, [trace], layout);
}

function createVolumeChart(data, container) {
    const trace = {
        x: data.dates,
        y: data.volume,
        type: 'bar',
        name: '成交量'
    };

    const layout = {
        title: '成交量',
        yaxis: {
            title: '成交量'
        },
        xaxis: {
            title: '日期'
        }
    };

    Plotly.newPlot(container, [trace], layout);
}

function createTechnicalIndicators(data, container) {
    const traces = [
        {
            x: data.dates,
            y: data.ma5,
            type: 'scatter',
            name: 'MA5'
        },
        {
            x: data.dates,
            y: data.ma10,
            type: 'scatter',
            name: 'MA10'
        },
        {
            x: data.dates,
            y: data.ma20,
            type: 'scatter',
            name: 'MA20'
        }
    ];

    const layout = {
        title: '技术指标',
        yaxis: {
            title: '价格'
        },
        xaxis: {
            title: '日期'
        }
    };

    Plotly.newPlot(container, traces, layout);
}

// 预测相关函数
function showPredictionResult(data) {
    const directionBadge = data.direction === 'up' 
        ? '<span class="badge bg-success">上涨</span>'
        : '<span class="badge bg-danger">下跌</span>';

    document.getElementById('prediction-direction').innerHTML = directionBadge;
    document.getElementById('prediction-price').textContent = data.predicted_price.toFixed(2);
    document.getElementById('prediction-confidence').textContent = data.confidence.toFixed(2) + '%';
    document.getElementById('prediction-date').textContent = new Date(data.date).toLocaleDateString();
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 初始化所有弹出框
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}); 
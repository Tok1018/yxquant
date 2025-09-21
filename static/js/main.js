// 主要JavaScript功能

// 全局变量
let charts = {};
let currentData = {};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

// 初始化页面
function initializePage() {
    // 添加页面动画
    addPageAnimations();
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化图表
    initializeCharts();
}

// 添加页面动画
function addPageAnimations() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// 初始化工具提示
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.classList.add('tooltip-custom');
    });
}

// 初始化图表
function initializeCharts() {
    // 这里可以初始化一些默认图表
    console.log('图表初始化完成');
}

// 显示加载状态
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="loading"></div> 加载中...';
    }
}

// 隐藏加载状态
function hideLoading(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content || '';
    }
}

// 显示消息
function showMessage(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const messageHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 在页面顶部显示消息
    const container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', messageHtml);
        
        // 3秒后自动隐藏
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 3000);
    }
}

// API请求封装
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API请求失败:', error);
        showMessage('请求失败: ' + error.message, 'error');
        throw error;
    }
}

// 格式化数字
function formatNumber(number, decimals = 2) {
    if (typeof number !== 'number') {
        return 'N/A';
    }
    
    if (number >= 1e9) {
        return (number / 1e9).toFixed(decimals) + 'B';
    } else if (number >= 1e6) {
        return (number / 1e6).toFixed(decimals) + 'M';
    } else if (number >= 1e3) {
        return (number / 1e3).toFixed(decimals) + 'K';
    } else {
        return number.toFixed(decimals);
    }
}

// 格式化百分比
function formatPercentage(number, decimals = 2) {
    if (typeof number !== 'number') {
        return 'N/A';
    }
    return (number * 100).toFixed(decimals) + '%';
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

// 格式化时间
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 创建图表
function createChart(canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas element with id '${canvasId}' not found`);
        return null;
    }
    
    const ctx = canvas.getContext('2d');
    const chart = new Chart(ctx, config);
    
    // 保存图表引用
    charts[canvasId] = chart;
    
    return chart;
}

// 更新图表
function updateChart(canvasId, newData) {
    const chart = charts[canvasId];
    if (chart) {
        chart.data = newData;
        chart.update();
    }
}

// 销毁图表
function destroyChart(canvasId) {
    const chart = charts[canvasId];
    if (chart) {
        chart.destroy();
        delete charts[canvasId];
    }
}

// 表格排序
function sortTable(table, column, ascending = true) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aVal = a.cells[column].textContent.trim();
        const bVal = b.cells[column].textContent.trim();
        
        // 尝试转换为数字
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        } else {
            return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }
    });
    
    // 重新排列行
    rows.forEach(row => tbody.appendChild(row));
}

// 表格搜索
function searchTable(table, searchTerm) {
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const matches = text.includes(searchTerm.toLowerCase());
        row.style.display = matches ? '' : 'none';
    });
}

// 导出数据为CSV
function exportToCSV(data, filename) {
    if (!data || data.length === 0) {
        showMessage('没有数据可导出', 'warning');
        return;
    }
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => row[header] || '').join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 复制到剪贴板
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showMessage('已复制到剪贴板', 'success');
    } catch (err) {
        console.error('复制失败:', err);
        showMessage('复制失败', 'error');
    }
}

// 验证股票代码格式
function validateSymbol(symbol) {
    const symbolRegex = /^[A-Z]{1,5}$/;
    return symbolRegex.test(symbol);
}

// 验证日期格式
function validateDate(dateString) {
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date);
}

// 获取URL参数
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 设置URL参数
function setUrlParameter(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.pushState({}, '', url);
}

// 页面刷新
function refreshPage() {
    window.location.reload();
}

// 页面跳转
function navigateTo(url) {
    window.location.href = url;
}

// 返回上一页
function goBack() {
    window.history.back();
}

// 控制台日志
function log(message, data = null) {
    if (data) {
        console.log(`[${new Date().toISOString()}] ${message}`, data);
    } else {
        console.log(`[${new Date().toISOString()}] ${message}`);
    }
}

// 错误处理
function handleError(error, context = '') {
    console.error(`[${context}] 错误:`, error);
    showMessage(`操作失败: ${error.message}`, 'error');
}

// 成功处理
function handleSuccess(message, data = null) {
    log(message, data);
    showMessage(message, 'success');
}

// Profit Analysis JavaScript
let profitTrendChart, revenueCostChart, categoryCharts = [];
let originalTableData = [];
let currentFilters = { search: '', sort: 'profit_desc', category: 'all' };

// Initialize all charts and functionality
function initializeProfitCharts() {
    initProfitTrendChart();
    initRevenueCostChart();
    initCategoryCharts();
    initAdvancedFilters();
    cacheTableData();
}

// Enhanced Profit Trend Chart with multiple datasets
function initProfitTrendChart() {
    const ctx = document.getElementById('profitTrendChart').getContext('2d');
    profitTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.profitTrend.labels,
            datasets: [{
                label: 'Profit',
                data: chartData.profitTrend.profits,
                borderColor: '#27ae60',
                backgroundColor: 'rgba(39, 174, 96, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }, {
                label: 'Revenue',
                data: chartData.profitTrend.revenue || [],
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.05)',
                borderWidth: 2,
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': Rs. ' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'Rs. ' + (value / 1000).toFixed(0) + 'K';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Revenue vs Cost Chart
function initRevenueCostChart() {
    const ctx = document.getElementById('revenueCostChart').getContext('2d');
    revenueCostChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.revenueCost.labels,
            datasets: [{
                label: 'Revenue',
                data: chartData.revenueCost.revenue,
                backgroundColor: '#27ae60',
                borderRadius: 6
            }, {
                label: 'Cost',
                data: chartData.revenueCost.cost,
                backgroundColor: '#e74c3c',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'Rs. ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Enhanced Category Charts with animations
function initCategoryCharts() {
    chartData.categories.forEach((category, index) => {
        const ctx = document.getElementById(`categoryChart${index + 1}`);
        if (ctx) {
            const chart = new Chart(ctx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Profit', 'Cost'],
                    datasets: [{
                        data: [category.profit, category.cost],
                        backgroundColor: ['#27ae60', '#e74c3c'],
                        borderWidth: 2,
                        borderColor: '#fff',
                        hoverBorderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '60%',
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.parsed / total) * 100).toFixed(1);
                                    return context.label + ': Rs. ' + context.parsed.toLocaleString() + ' (' + percentage + '%)';
                                }
                            }
                        }
                    },
                    animation: {
                        animateRotate: true,
                        duration: 1000
                    }
                }
            });
            categoryCharts.push(chart);
        }
    });
}

// Enhanced Table Filtering and Sorting
function setupTableFilters() {
    const searchInput = document.getElementById('productSearch');
    const sortSelect = document.getElementById('sortBy');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            currentFilters.search = this.value.toLowerCase();
            applyFilters();
        }, 300));
    }
    
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            currentFilters.sort = this.value;
            applyFilters();
        });
    }
}

// Initialize advanced filters
function initAdvancedFilters() {
    // Add category filter if not exists
    const tableControls = document.querySelector('.table-controls');
    if (tableControls && !document.getElementById('categoryFilter')) {
        const categoryFilter = document.createElement('select');
        categoryFilter.id = 'categoryFilter';
        categoryFilter.innerHTML = `
            <option value="all">All Categories</option>
            <option value="electronics">Electronics</option>
            <option value="clothing">Clothing</option>
            <option value="food">Food & Beverages</option>
            <option value="books">Books</option>
            <option value="other">Other</option>
        `;
        categoryFilter.addEventListener('change', function() {
            currentFilters.category = this.value;
            applyFilters();
        });
        tableControls.appendChild(categoryFilter);
    }
    
    // Add export button to table controls
    if (tableControls && !document.getElementById('exportTableBtn')) {
        const exportBtn = document.createElement('button');
        exportBtn.id = 'exportTableBtn';
        exportBtn.textContent = '📊 Export Table';
        exportBtn.className = 'btn-export';
        exportBtn.style.marginLeft = '10px';
        exportBtn.onclick = exportTableToCSV;
        tableControls.appendChild(exportBtn);
    }
}

// Cache original table data
function cacheTableData() {
    const table = document.getElementById('profitabilityTable');
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    
    originalTableData = Array.from(rows).map(row => ({
        element: row.cloneNode(true),
        name: row.cells[0].textContent.toLowerCase(),
        quantity: parseInt(row.cells[1].textContent),
        revenue: parseFloat(row.cells[2].textContent.replace(/[Rs.,\s]/g, '')),
        cost: parseFloat(row.cells[3].textContent.replace(/[Rs.,\s]/g, '')),
        profit: parseFloat(row.cells[4].textContent.replace(/[Rs.,\s]/g, '')),
        margin: parseFloat(row.cells[5].textContent.replace('%', '')),
        category: row.dataset.category || 'other'
    }));
}

// Enhanced filtering and sorting
function applyFilters() {
    let filteredData = [...originalTableData];
    
    // Apply search filter
    if (currentFilters.search) {
        filteredData = filteredData.filter(item => 
            item.name.includes(currentFilters.search)
        );
    }
    
    // Apply category filter
    if (currentFilters.category !== 'all') {
        filteredData = filteredData.filter(item => 
            item.category === currentFilters.category
        );
    }
    
    // Apply sorting
    filteredData.sort((a, b) => {
        switch(currentFilters.sort) {
            case 'profit_desc': return b.profit - a.profit;
            case 'profit_asc': return a.profit - b.profit;
            case 'margin_desc': return b.margin - a.margin;
            case 'margin_asc': return a.margin - b.margin;
            case 'quantity_desc': return b.quantity - a.quantity;
            case 'quantity_asc': return a.quantity - b.quantity;
            case 'revenue_desc': return b.revenue - a.revenue;
            case 'revenue_asc': return a.revenue - b.revenue;
            case 'name_asc': return a.name.localeCompare(b.name);
            case 'name_desc': return b.name.localeCompare(a.name);
            default: return 0;
        }
    });
    
    // Update table
    updateTableDisplay(filteredData);
    updateTableStats(filteredData);
}

function updateTableDisplay(data) {
    const tbody = document.querySelector('#profitabilityTable tbody');
    tbody.innerHTML = '';
    
    data.forEach(item => {
        tbody.appendChild(item.element.cloneNode(true));
    });
    
    // Add row click handlers for details
    tbody.querySelectorAll('tr').forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => showProductDetails(row));
    });
}

function updateTableStats(data) {
    const totalItems = data.length;
    const totalRevenue = data.reduce((sum, item) => sum + item.revenue, 0);
    const totalProfit = data.reduce((sum, item) => sum + item.profit, 0);
    const avgMargin = totalRevenue > 0 ? (totalProfit / totalRevenue) * 100 : 0;
    
    // Update or create stats display
    let statsDiv = document.getElementById('tableStats');
    if (!statsDiv) {
        statsDiv = document.createElement('div');
        statsDiv.id = 'tableStats';
        statsDiv.className = 'table-stats';
        document.querySelector('.profitability-table').appendChild(statsDiv);
    }
    
    statsDiv.innerHTML = `
        <div class="stats-grid">
            <div class="stat-item">
                <span class="stat-label">Products:</span>
                <span class="stat-value">${totalItems}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Total Revenue:</span>
                <span class="stat-value">Rs. ${totalRevenue.toLocaleString()}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Total Profit:</span>
                <span class="stat-value">Rs. ${totalProfit.toLocaleString()}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Avg Margin:</span>
                <span class="stat-value">${avgMargin.toFixed(1)}%</span>
            </div>
        </div>
    `;
}

// Period Filter
function setupPeriodFilter() {
    const periodFilter = document.getElementById('periodFilter');
    if (periodFilter) {
        periodFilter.addEventListener('change', function() {
            updateAnalysis(this.value);
        });
    }
}

function updateAnalysis(period) {
    // Show loading state
    showLoading();
    
    // Fetch new data
    fetch(`/reports/profit-analysis/?period=${period}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        updateMetrics(data.metrics);
        updateCharts(data.charts);
        updateTable(data.products);
        hideLoading();
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
    });
}

function updateMetrics(metrics) {
    document.querySelector('.revenue .metric-value').textContent = `Rs. ${metrics.total_revenue.toLocaleString()}`;
    document.querySelector('.profit .metric-value').textContent = `Rs. ${metrics.net_profit.toLocaleString()}`;
    document.querySelector('.margin .metric-value').textContent = `${metrics.profit_margin.toFixed(1)}%`;
    document.querySelector('.cost .metric-value').textContent = `Rs. ${metrics.total_cost.toLocaleString()}`;
}

function updateCharts(chartData) {
    // Update profit trend chart
    profitTrendChart.data.labels = chartData.profitTrend.labels;
    profitTrendChart.data.datasets[0].data = chartData.profitTrend.profits;
    profitTrendChart.update();
    
    // Update revenue cost chart
    revenueCostChart.data.labels = chartData.revenueCost.labels;
    revenueCostChart.data.datasets[0].data = chartData.revenueCost.revenue;
    revenueCostChart.data.datasets[1].data = chartData.revenueCost.cost;
    revenueCostChart.update();
}

function updateTable(products) {
    const tbody = document.querySelector('#profitabilityTable tbody');
    tbody.innerHTML = '';
    
    products.forEach(product => {
        const row = `
            <tr>
                <td>${product.name}</td>
                <td>${product.quantity_sold}</td>
                <td>Rs. ${product.revenue.toLocaleString()}</td>
                <td>Rs. ${product.cost.toLocaleString()}</td>
                <td class="profit-cell">Rs. ${product.profit.toLocaleString()}</td>
                <td>${product.margin.toFixed(1)}%</td>
                <td>
                    <div class="performance-bar">
                        <div class="bar-fill" style="width: ${product.performance}%"></div>
                    </div>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

// Enhanced Export Functions
function exportTableToCSV() {
    const table = document.getElementById('profitabilityTable');
    const rows = table.querySelectorAll('tr');
    let csvContent = '';
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            return '"' + col.textContent.replace(/"/g, '""') + '"';
        }).join(',');
        csvContent += rowData + '\n';
    });
    
    downloadFile(csvContent, 'profit-analysis-table.csv', 'text/csv');
}

function exportToPDF() {
    showLoading();
    
    fetch('/reports/export-profit-pdf/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            period: document.getElementById('periodFilter').value
        })
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `profit-analysis-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        hideLoading();
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
    });
}

function exportToExcel() {
    showLoading();
    
    fetch('/reports/export-profit-excel/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            period: document.getElementById('periodFilter').value
        })
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `profit-analysis-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        hideLoading();
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
    });
}

function shareWhatsApp() {
    const period = document.getElementById('periodFilter').value;
    const revenue = document.querySelector('.revenue .metric-value').textContent;
    const profit = document.querySelector('.profit .metric-value').textContent;
    const margin = document.querySelector('.margin .metric-value').textContent;
    const cost = document.querySelector('.cost .metric-value').textContent;
    
    const message = `📊 *ShopCloud Profit Analysis*\n\n` +
                   `📅 Period: ${period.charAt(0).toUpperCase() + period.slice(1)}\n` +
                   `💰 Revenue: ${revenue}\n` +
                   `📈 Profit: ${profit}\n` +
                   `💸 Cost: ${cost}\n` +
                   `📊 Margin: ${margin}\n\n` +
                   `🔗 Generated by ShopCloud POS\n` +
                   `📱 Get ShopCloud: [Your App Link]`;
    
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
}

// Enhanced Utility Functions
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

function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    showNotification(`${filename} downloaded successfully`, 'success');
}

function showProductDetails(row) {
    const productName = row.cells[0].textContent;
    const quantity = row.cells[1].textContent;
    const revenue = row.cells[2].textContent;
    const cost = row.cells[3].textContent;
    const profit = row.cells[4].textContent;
    const margin = row.cells[5].textContent;
    
    const modal = document.createElement('div');
    modal.className = 'product-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>📊 ${productName} - Detailed Analysis</h3>
                <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">Quantity Sold:</span>
                        <span class="detail-value">${quantity}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Total Revenue:</span>
                        <span class="detail-value">${revenue}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Total Cost:</span>
                        <span class="detail-value">${cost}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Net Profit:</span>
                        <span class="detail-value profit">${profit}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Profit Margin:</span>
                        <span class="detail-value">${margin}</span>
                    </div>
                </div>
                <div class="action-buttons">
                    <button onclick="generateProductReport('${productName}')" class="btn-action">📈 Generate Report</button>
                    <button onclick="shareProductData('${productName}')" class="btn-action">📱 Share</button>
                </div>
            </div>
        </div>
    `;
    
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    document.body.appendChild(modal);
}

function generateProductReport(productName) {
    showNotification(`Generating detailed report for ${productName}...`, 'info');
    // Implementation for product-specific report generation
}

function shareProductData(productName) {
    const message = `📊 Product Analysis: ${productName}\n\nGenerated by ShopCloud POS`;
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
}

function printReport() {
    const printWindow = window.open('', '_blank');
    const printContent = generatePrintableReport();
    
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
    
    showNotification('Print dialog opened', 'info');
}

function emailReport() {
    const period = document.getElementById('periodFilter').value;
    const revenue = document.querySelector('.revenue .metric-value').textContent;
    const profit = document.querySelector('.profit .metric-value').textContent;
    const margin = document.querySelector('.margin .metric-value').textContent;
    
    const subject = `ShopCloud Profit Analysis - ${period.charAt(0).toUpperCase() + period.slice(1)}`;
    const body = `Dear Team,\n\nPlease find the profit analysis summary below:\n\n` +
                `Period: ${period.charAt(0).toUpperCase() + period.slice(1)}\n` +
                `Revenue: ${revenue}\n` +
                `Profit: ${profit}\n` +
                `Margin: ${margin}\n\n` +
                `For detailed analysis, please access the ShopCloud dashboard.\n\n` +
                `Best regards,\nShopCloud System`;
    
    const mailtoUrl = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoUrl;
    
    showNotification('Email client opened', 'info');
}

function generatePrintableReport() {
    const period = document.getElementById('periodFilter').value;
    const revenue = document.querySelector('.revenue .metric-value').textContent;
    const profit = document.querySelector('.profit .metric-value').textContent;
    const margin = document.querySelector('.margin .metric-value').textContent;
    const cost = document.querySelector('.cost .metric-value').textContent;
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>ShopCloud Profit Analysis Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px; }
                .metric { padding: 15px; border: 1px solid #ddd; border-radius: 8px; }
                .metric-label { font-size: 14px; color: #666; margin-bottom: 5px; }
                .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
                .table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                .table th, .table td { padding: 10px; border: 1px solid #ddd; text-align: left; }
                .table th { background: #f8f9fa; }
                .footer { margin-top: 30px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 ShopCloud Profit Analysis Report</h1>
                <p>Period: ${period.charAt(0).toUpperCase() + period.slice(1)} | Generated: ${new Date().toLocaleDateString()}</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Total Revenue</div>
                    <div class="metric-value">${revenue}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Net Profit</div>
                    <div class="metric-value">${profit}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Profit Margin</div>
                    <div class="metric-value">${margin}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Cost</div>
                    <div class="metric-value">${cost}</div>
                </div>
            </div>
            
            <div class="footer">
                <p>Generated by ShopCloud POS System | © ${new Date().getFullYear()}</p>
            </div>
        </body>
        </html>
    `;
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        border-radius: 8px;
        z-index: 10001;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showLoading() {
    const loader = document.createElement('div');
    loader.id = 'loadingOverlay';
    loader.innerHTML = `
        <div class="spinner-container">
            <div class="spinner"></div>
            <div class="loading-text">Loading...</div>
        </div>
    `;
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        color: white;
        font-size: 18px;
    `;
    document.body.appendChild(loader);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .spinner-container {
        text-align: center;
    }
    
    .spinner {
        border: 4px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top: 4px solid #fff;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .product-modal .modal-content {
        background: white;
        border-radius: 12px;
        padding: 0;
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    .modal-header {
        padding: 20px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .close-btn {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #999;
    }
    
    .modal-body {
        padding: 20px;
    }
    
    .detail-grid {
        display: grid;
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .detail-item {
        display: flex;
        justify-content: space-between;
        padding: 10px;
        background: #f8f9fa;
        border-radius: 6px;
    }
    
    .detail-label {
        font-weight: 600;
        color: #666;
    }
    
    .detail-value {
        font-weight: bold;
        color: #2c3e50;
    }
    
    .detail-value.profit {
        color: #27ae60;
    }
    
    .action-buttons {
        display: flex;
        gap: 10px;
        justify-content: center;
    }
    
    .btn-action {
        padding: 10px 20px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
    }
    
    .btn-action:hover {
        background: #2980b9;
    }
    
    .table-stats {
        margin-top: 20px;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 8px;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-label {
        display: block;
        font-size: 12px;
        color: #666;
        margin-bottom: 5px;
    }
    
    .stat-value {
        display: block;
        font-size: 16px;
        font-weight: bold;
        color: #2c3e50;
    }
`;
document.head.appendChild(style);

function hideLoading() {
    const loader = document.getElementById('loadingOverlay');
    if (loader) {
        loader.remove();
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Local storage for user preferences
function saveUserPreferences() {
    const preferences = {
        period: document.getElementById('periodFilter').value,
        sort: currentFilters.sort,
        category: currentFilters.category
    };
    localStorage.setItem('profitAnalysisPrefs', JSON.stringify(preferences));
}

function loadUserPreferences() {
    const saved = localStorage.getItem('profitAnalysisPrefs');
    if (saved) {
        const preferences = JSON.parse(saved);
        
        if (preferences.period) {
            document.getElementById('periodFilter').value = preferences.period;
        }
        if (preferences.sort) {
            currentFilters.sort = preferences.sort;
            const sortSelect = document.getElementById('sortBy');
            if (sortSelect) sortSelect.value = preferences.sort;
        }
        if (preferences.category) {
            currentFilters.category = preferences.category;
            const categoryFilter = document.getElementById('categoryFilter');
            if (categoryFilter) categoryFilter.value = preferences.category;
        }
    }
}

// Enhanced Real-time Updates and Keyboard Shortcuts
function startRealTimeUpdates() {
    setInterval(() => {
        const currentPeriod = document.getElementById('periodFilter').value;
        if (currentPeriod === 'today') {
            updateAnalysis('today');
        }
    }, 300000); // Update every 5 minutes for today's data
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'e':
                    e.preventDefault();
                    exportToExcel();
                    break;
                case 'p':
                    e.preventDefault();
                    exportToPDF();
                    break;
                case 'f':
                    e.preventDefault();
                    document.getElementById('productSearch').focus();
                    break;
                case 'r':
                    e.preventDefault();
                    refreshData();
                    break;
            }
        }
        
        if (e.key === 'Escape') {
            document.querySelectorAll('.product-modal').forEach(modal => modal.remove());
        }
    });
}

// Data refresh functionality
function refreshData() {
    showLoading();
    const currentPeriod = document.getElementById('periodFilter').value;
    updateAnalysis(currentPeriod);
}

// Initialize enhanced features
document.addEventListener('DOMContentLoaded', function() {
    startRealTimeUpdates();
    setupKeyboardShortcuts();
    addHelpTooltip();
});

function addHelpTooltip() {
    const helpBtn = document.createElement('button');
    helpBtn.innerHTML = '❓';
    helpBtn.className = 'help-btn';
    helpBtn.title = 'Keyboard Shortcuts: Ctrl+E (Excel), Ctrl+P (PDF), Ctrl+F (Search), Ctrl+R (Refresh)';
    helpBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #3498db;
        color: white;
        border: none;
        font-size: 20px;
        cursor: pointer;
        z-index: 1000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    `;
    
    helpBtn.onclick = function() {
        showNotification('Keyboard Shortcuts:\nCtrl+E: Export Excel\nCtrl+P: Export PDF\nCtrl+F: Focus Search\nCtrl+R: Refresh Data\nEsc: Close Modals', 'info');
    };
    
    document.body.appendChild(helpBtn);
}
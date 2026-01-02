// Sample Data Generator for Profit Analysis Testing
// This file provides sample data for testing the profit analysis functionality

// Generate sample chart data
function generateSampleChartData() {
    const labels = [];
    const profits = [];
    const revenue = [];
    const costs = [];
    
    // Generate 30 days of sample data
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Generate realistic profit data with some variation
        const baseProfit = 15000 + Math.random() * 10000;
        const baseRevenue = baseProfit * (2 + Math.random());
        const baseCost = baseRevenue - baseProfit;
        
        profits.push(Math.round(baseProfit));
        revenue.push(Math.round(baseRevenue));
        costs.push(Math.round(baseCost));
    }
    
    return {
        profitTrend: {
            labels: labels,
            profits: profits,
            revenue: revenue
        },
        revenueCost: {
            labels: labels.slice(-7), // Last 7 days
            revenue: revenue.slice(-7),
            cost: costs.slice(-7)
        },
        categories: [
            { name: 'Electronics', profit: 45000, cost: 85000 },
            { name: 'Clothing', profit: 32000, cost: 48000 },
            { name: 'Food & Beverages', profit: 28000, cost: 42000 },
            { name: 'Books', profit: 15000, cost: 25000 },
            { name: 'Other', profit: 12000, cost: 18000 }
        ]
    };
}

// Generate sample product data
function generateSampleProductData() {
    const products = [
        { name: 'Samsung Galaxy S23', category: 'electronics', basePrice: 120000, baseCost: 95000 },
        { name: 'iPhone 14 Pro', category: 'electronics', basePrice: 180000, baseCost: 145000 },
        { name: 'Dell Laptop XPS 13', category: 'electronics', basePrice: 85000, baseCost: 68000 },
        { name: 'Nike Air Max', category: 'clothing', basePrice: 12000, baseCost: 7500 },
        { name: 'Adidas Hoodie', category: 'clothing', basePrice: 8000, baseCost: 5200 },
        { name: 'Levi\'s Jeans', category: 'clothing', basePrice: 6500, baseCost: 4000 },
        { name: 'Coca Cola 1.5L', category: 'food', basePrice: 150, baseCost: 95 },
        { name: 'Lay\'s Chips', category: 'food', basePrice: 80, baseCost: 50 },
        { name: 'Nestle Water', category: 'food', basePrice: 60, baseCost: 35 },
        { name: 'Harry Potter Book', category: 'books', basePrice: 1200, baseCost: 800 },
        { name: 'Programming Guide', category: 'books', basePrice: 2500, baseCost: 1600 },
        { name: 'Notebook A4', category: 'other', basePrice: 250, baseCost: 150 },
        { name: 'Pen Set', category: 'other', basePrice: 180, baseCost: 110 },
        { name: 'Phone Case', category: 'electronics', basePrice: 800, baseCost: 450 },
        { name: 'Bluetooth Speaker', category: 'electronics', basePrice: 3500, baseCost: 2200 }
    ];
    
    return products.map(product => {
        const quantity = Math.floor(Math.random() * 50) + 1;
        const revenue = product.basePrice * quantity;
        const cost = product.baseCost * quantity;
        const profit = revenue - cost;
        const margin = (profit / revenue) * 100;
        const performance = Math.min((profit / 10000) * 100, 100); // Normalize to 0-100
        
        return {
            name: product.name,
            category: product.category,
            quantity_sold: quantity,
            revenue: revenue,
            cost: cost,
            profit: profit,
            margin: margin,
            performance: performance
        };
    });
}

// Generate sample metrics
function generateSampleMetrics() {
    const products = generateSampleProductData();
    const totalRevenue = products.reduce((sum, p) => sum + p.revenue, 0);
    const totalCost = products.reduce((sum, p) => sum + p.cost, 0);
    const netProfit = totalRevenue - totalCost;
    const profitMargin = (netProfit / totalRevenue) * 100;
    
    return {
        total_revenue: totalRevenue,
        total_cost: totalCost,
        net_profit: netProfit,
        profit_margin: profitMargin,
        revenue_change: (Math.random() * 20 - 5).toFixed(1), // -5% to +15%
        profit_change: (Math.random() * 25 - 5).toFixed(1),  // -5% to +20%
        cost_change: (Math.random() * 15 - 10).toFixed(1),   // -10% to +5%
        margin_trend: Math.random() > 0.5 ? 'Improving' : 'Stable'
    };
}

// Generate sample category analysis
function generateSampleCategoryAnalysis() {
    const categories = ['Electronics', 'Clothing', 'Food & Beverages', 'Books', 'Other'];
    
    return categories.map(category => {
        const revenue = Math.floor(Math.random() * 100000) + 50000;
        const cost = Math.floor(revenue * (0.6 + Math.random() * 0.2)); // 60-80% of revenue
        const profit = revenue - cost;
        const margin = (profit / revenue) * 100;
        
        return {
            name: category,
            revenue: revenue,
            cost: cost,
            profit: profit,
            margin: margin
        };
    });
}

// Generate AI insights
function generateSampleAIInsights() {
    const recommendations = [
        'Consider increasing prices for high-demand electronics by 5-8%',
        'Focus marketing efforts on clothing items with highest margins',
        'Optimize inventory for fast-moving food & beverage products',
        'Bundle slow-moving books with popular electronics',
        'Negotiate better wholesale prices for items with margins below 15%'
    ];
    
    const alerts = [
        { type: 'warning', message: '3 products have margins below 10%' },
        { type: 'info', message: 'Electronics category showing 15% growth this month' },
        { type: 'danger', message: 'Inventory running low for 5 high-profit items' }
    ];
    
    return {
        ai_recommendations: recommendations,
        profit_alerts: alerts
    };
}

// Initialize sample data if no real data is available
function initializeSampleData() {
    // Check if chartData is already defined (from Django template)
    if (typeof chartData === 'undefined') {
        window.chartData = generateSampleChartData();
    }
    
    // Add sample data to global scope for testing
    window.sampleData = {
        metrics: generateSampleMetrics(),
        products: generateSampleProductData(),
        categories: generateSampleCategoryAnalysis(),
        insights: generateSampleAIInsights()
    };
    
    console.log('Sample data initialized:', window.sampleData);
}

// Demo mode toggle
function toggleDemoMode() {
    const isDemoMode = localStorage.getItem('profitAnalysisDemoMode') === 'true';
    
    if (!isDemoMode) {
        // Enable demo mode
        localStorage.setItem('profitAnalysisDemoMode', 'true');
        loadDemoData();
        showNotification('Demo mode enabled - using sample data', 'info');
    } else {
        // Disable demo mode
        localStorage.setItem('profitAnalysisDemoMode', 'false');
        location.reload(); // Reload to get real data
    }
}

function loadDemoData() {
    const sampleData = window.sampleData;
    
    // Update metrics
    updateMetrics(sampleData.metrics);
    
    // Update charts
    updateCharts(generateSampleChartData());
    
    // Update table
    updateTable(sampleData.products);
    
    // Add demo mode indicator
    addDemoModeIndicator();
}

function addDemoModeIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'demoIndicator';
    indicator.innerHTML = '🎭 Demo Mode - <button onclick="toggleDemoMode()">Exit Demo</button>';
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        background: #f39c12;
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        z-index: 10000;
        font-size: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    `;
    
    indicator.querySelector('button').style.cssText = `
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
        color: white;
        padding: 5px 10px;
        border-radius: 10px;
        cursor: pointer;
        margin-left: 10px;
    `;
    
    document.body.appendChild(indicator);
}

// Check for demo mode on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeSampleData();
    
    if (localStorage.getItem('profitAnalysisDemoMode') === 'true') {
        setTimeout(() => {
            loadDemoData();
        }, 1000); // Delay to ensure other scripts are loaded
    }
    
    // Add demo mode toggle to help menu
    const helpBtn = document.querySelector('.help-btn');
    if (helpBtn) {
        helpBtn.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            toggleDemoMode();
        });
    }
});

// Export functions for external use
window.ProfitAnalysisDemo = {
    generateSampleChartData,
    generateSampleProductData,
    generateSampleMetrics,
    toggleDemoMode,
    loadDemoData
};
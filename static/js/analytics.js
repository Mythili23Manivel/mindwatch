// MindWatch - Analytics Dashboard JavaScript

// Global variables
let analyticsData = null;
let charts = {};

// Initialize analytics when data is loaded
function initializeAnalytics(data) {
    analyticsData = data;
    console.log('Initializing analytics with data:', data);
    
    // Initialize all charts
    initializeCharts();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initialize data tables if present
    initializeDataTables();
}

function initializeCharts() {
    if (!analyticsData || !analyticsData.summary) {
        console.warn('No analytics data available');
        return;
    }
    
    const { summary, fileType } = analyticsData;
    
    // Initialize activity distribution chart
    if (document.getElementById('activityDistributionChart')) {
        createActivityDistributionChart(summary);
    }
    
    // Initialize engagement pie chart
    if (document.getElementById('engagementPieChart')) {
        createEngagementPieChart(summary, fileType);
    }
    
    // Initialize performance heatmap (video only)
    if (document.getElementById('performanceHeatmap') && fileType === 'video') {
        createPerformanceHeatmap(summary);
    }
    
    // Initialize timeline chart (video only)
    if (document.getElementById('timelineChart') && fileType === 'video') {
        createTimelineChart(summary);
    }
}

function createActivityDistributionChart(summary) {
    const ctx = document.getElementById('activityDistributionChart').getContext('2d');
    const activityBreakdown = summary.activity_breakdown || {};
    
    const labels = Object.keys(activityBreakdown).map(label => 
        label.charAt(0).toUpperCase() + label.slice(1).replace('_', ' ')
    );
    const data = Object.values(activityBreakdown);
    const colors = MindWatch.getChartColorPalette();
    
    charts.activityDistribution = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Detections',
                data: data,
                backgroundColor: colors.slice(0, data.length),
                borderColor: colors.slice(0, data.length).map(color => color.replace('0.8', '1')),
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Activity Distribution Analysis',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: '#007bff',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const total = data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `Count: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        font: { size: 12 },
                        maxRotation: 45
                    },
                    grid: {
                        display: false
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}

function createEngagementPieChart(summary, fileType) {
    const ctx = document.getElementById('engagementPieChart').getContext('2d');
    
    let attentiveCount, distractedCount;
    
    if (fileType === 'image') {
        attentiveCount = summary.attentive_students || 0;
        distractedCount = summary.distracted_students || 0;
    } else if (fileType === 'video' && summary.student_analysis) {
        const studentAnalysis = summary.student_analysis;
        attentiveCount = Object.values(studentAnalysis).filter(s => s.classification === 'Attentive').length;
        distractedCount = Object.values(studentAnalysis).length - attentiveCount;
    } else {
        attentiveCount = 0;
        distractedCount = 0;
    }
    
    charts.engagementPie = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Attentive', 'Distracted'],
            datasets: [{
                data: [attentiveCount, distractedCount],
                backgroundColor: ['#28a745', '#dc3545'],
                borderColor: ['#1e7e34', '#c82333'],
                borderWidth: 2,
                hoverBackgroundColor: ['#34ce57', '#e14c5c'],
                hoverBorderColor: ['#1e7e34', '#c82333'],
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Engagement Overview',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: { size: 14 }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    callbacks: {
                        label: function(context) {
                            const total = attentiveCount + distractedCount;
                            const percentage = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%',
            animation: {
                animateScale: true,
                animateRotate: true,
                duration: 1000
            }
        }
    });
}

function createPerformanceHeatmap(summary) {
    if (!summary.student_analysis) return;
    
    const ctx = document.getElementById('performanceHeatmap').getContext('2d');
    const studentAnalysis = summary.student_analysis;
    
    // Prepare data for heatmap
    const students = Object.keys(studentAnalysis);
    const activities = ['listening', 'reading', 'writing', 'sleeping', 'using_mobile', 'turn'];
    
    const datasets = activities.map((activity, index) => {
        const data = students.map(studentId => {
            const studentData = studentAnalysis[studentId];
            const activityCount = studentData.activity_breakdown[activity] || 0;
            const totalDetections = studentData.total_detections;
            return totalDetections > 0 ? (activityCount / totalDetections) * 100 : 0;
        });
        
        return {
            label: activity.charAt(0).toUpperCase() + activity.slice(1).replace('_', ' '),
            data: data,
            backgroundColor: MindWatch.getChartColorPalette()[index],
            borderColor: 'white',
            borderWidth: 1
        };
    });
    
    charts.performanceHeatmap = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: students,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Student Performance Heatmap',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: { font: { size: 10 } }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function createTimelineChart(summary) {
    if (!summary.student_analysis) return;
    
    const ctx = document.getElementById('timelineChart').getContext('2d');
    const studentAnalysis = summary.student_analysis;
    
    // Create timeline data - simplified version showing engagement over time
    const timePoints = [];
    const engagementData = [];
    
    // Sample time points (this would be more detailed with actual timeline data)
    for (let i = 0; i <= 10; i++) {
        timePoints.push(i * (summary.video_duration / 10));
        
        // Calculate average engagement at this time point
        let totalEngagement = 0;
        let studentCount = 0;
        
        Object.values(studentAnalysis).forEach(student => {
            totalEngagement += student.attentive_percentage;
            studentCount++;
        });
        
        // Add some variation for demo
        const baseEngagement = studentCount > 0 ? totalEngagement / studentCount : 0;
        const variation = (Math.random() - 0.5) * 20; // ±10% variation
        engagementData.push(Math.max(0, Math.min(100, baseEngagement + variation)));
    });
    
    charts.timeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timePoints.map(t => `${Math.floor(t / 60)}:${(t % 60).toFixed(0).padStart(2, '0')}`),
            datasets: [{
                label: 'Engagement Level',
                data: engagementData,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#007bff',
                pointBorderColor: 'white',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Engagement Timeline',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `Engagement: ${context.raw.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time (mm:ss)',
                        font: { size: 12, weight: 'bold' }
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Engagement Level (%)',
                        font: { size: 12, weight: 'bold' }
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function setupEventListeners() {
    // Chart export buttons
    document.querySelectorAll('[data-chart-export]').forEach(button => {
        button.addEventListener('click', function() {
            const chartId = this.dataset.chartExport;
            exportChart(chartId);
        });
    });
    
    // Data refresh button
    const refreshButton = document.getElementById('refreshData');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshAnalytics);
    }
    
    // Filter controls
    setupFilterControls();
    
    // Chart resize handler
    window.addEventListener('resize', MindWatch.debounce(() => {
        Object.values(charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }, 250));
}

function setupFilterControls() {
    // Activity filter
    const activityFilter = document.getElementById('activityFilter');
    if (activityFilter) {
        activityFilter.addEventListener('change', function() {
            filterChartsByActivity(this.value);
        });
    }
    
    // Time range filter (for video analysis)
    const timeRangeFilter = document.getElementById('timeRangeFilter');
    if (timeRangeFilter) {
        timeRangeFilter.addEventListener('change', function() {
            filterChartsByTimeRange(this.value);
        });
    }
}

function initializeDataTables() {
    // Initialize sortable tables
    const tables = document.querySelectorAll('.sortable-table');
    tables.forEach(table => {
        makeSortable(table);
    });
}

function makeSortable(table) {
    const headers = table.querySelectorAll('th[data-sortable]');
    
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="fas fa-sort text-muted"></i>';
        
        header.addEventListener('click', function() {
            const column = this.dataset.sortable;
            const currentOrder = this.dataset.order || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            
            // Reset all headers
            headers.forEach(h => {
                h.dataset.order = '';
                const icon = h.querySelector('i');
                if (icon) {
                    icon.className = 'fas fa-sort text-muted';
                }
            });
            
            // Set current header
            this.dataset.order = newOrder;
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = `fas fa-sort-${newOrder === 'asc' ? 'up' : 'down'} text-primary`;
            }
            
            sortTable(table, column, newOrder);
        });
    });
}

function sortTable(table, column, order) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.querySelector(`[data-column="${column}"]`)?.textContent || '';
        const bValue = b.querySelector(`[data-column="${column}"]`)?.textContent || '';
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue.replace(/[^\d.-]/g, ''));
        const bNum = parseFloat(bValue.replace(/[^\d.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return order === 'asc' ? aNum - bNum : bNum - aNum;
        } else {
            return order === 'asc' 
                ? aValue.localeCompare(bValue)
                : bValue.localeCompare(aValue);
        }
    });
    
    // Reattach sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

function filterChartsByActivity(activity) {
    if (!activity || activity === 'all') {
        // Show all data
        refreshCharts();
        return;
    }
    
    // Filter charts to show only selected activity
    // This would require rebuilding charts with filtered data
    console.log('Filtering by activity:', activity);
    // Implementation would depend on specific requirements
}

function filterChartsByTimeRange(range) {
    if (!range || range === 'all') {
        refreshCharts();
        return;
    }
    
    console.log('Filtering by time range:', range);
    // Implementation would filter timeline data
}

function refreshAnalytics() {
    if (!analyticsData || !analyticsData.sessionId) return;
    
    const refreshButton = document.getElementById('refreshData');
    if (refreshButton) {
        MindWatch.showLoading(refreshButton);
    }
    
    // Fetch fresh data
    fetch(`/api/analytics/${analyticsData.sessionId}`)
        .then(response => response.json())
        .then(data => {
            analyticsData.summary = data;
            refreshCharts();
            MindWatch.showNotification('Analytics data refreshed', 'success');
        })
        .catch(error => {
            console.error('Failed to refresh data:', error);
            MindWatch.showNotification('Failed to refresh data', 'danger');
        })
        .finally(() => {
            if (refreshButton) {
                MindWatch.hideLoading(refreshButton);
            }
        });
}

function refreshCharts() {
    // Destroy existing charts
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    
    charts = {};
    
    // Reinitialize charts
    setTimeout(() => {
        initializeCharts();
    }, 100);
}

function exportChart(chartId) {
    const chart = charts[chartId];
    if (!chart) {
        MindWatch.showNotification('Chart not found', 'warning');
        return;
    }
    
    try {
        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = `mindwatch_${chartId}_${Date.now()}.png`;
        link.href = url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        MindWatch.showNotification('Chart exported successfully', 'success');
    } catch (error) {
        console.error('Failed to export chart:', error);
        MindWatch.showNotification('Failed to export chart', 'danger');
    }
}

// Utility functions
function calculateEngagementMetrics(summary, fileType) {
    const metrics = {};
    
    if (fileType === 'image') {
        const total = summary.total_students || 0;
        const attentive = summary.attentive_students || 0;
        
        metrics.engagementRate = total > 0 ? (attentive / total) * 100 : 0;
        metrics.distractionRate = 100 - metrics.engagementRate;
        metrics.totalStudents = total;
        metrics.attentiveStudents = attentive;
        metrics.distractedStudents = total - attentive;
    } else if (fileType === 'video' && summary.student_analysis) {
        const studentData = Object.values(summary.student_analysis);
        
        if (studentData.length > 0) {
            const attentivePercentages = studentData.map(s => s.attentive_percentage);
            
            metrics.avgEngagement = attentivePercentages.reduce((a, b) => a + b, 0) / attentivePercentages.length;
            metrics.minEngagement = Math.min(...attentivePercentages);
            metrics.maxEngagement = Math.max(...attentivePercentages);
            metrics.engagementVariation = metrics.maxEngagement - metrics.minEngagement;
            
            metrics.totalStudents = studentData.length;
            metrics.attentiveStudents = studentData.filter(s => s.classification === 'Attentive').length;
            metrics.distractedStudents = metrics.totalStudents - metrics.attentiveStudents;
        }
    }
    
    return metrics;
}

function generateInsights(summary, fileType) {
    const insights = [];
    const metrics = calculateEngagementMetrics(summary, fileType);
    
    if (metrics.engagementRate > 80) {
        insights.push({
            type: 'success',
            text: `Excellent engagement rate of ${metrics.engagementRate.toFixed(1)}%`
        });
    } else if (metrics.engagementRate > 60) {
        insights.push({
            type: 'info',
            text: `Good engagement rate of ${metrics.engagementRate.toFixed(1)}%`
        });
    } else {
        insights.push({
            type: 'warning',
            text: `Low engagement rate of ${metrics.engagementRate.toFixed(1)}% - needs attention`
        });
    }
    
    if (fileType === 'video' && metrics.engagementVariation > 30) {
        insights.push({
            type: 'warning',
            text: `High engagement variation (${metrics.engagementVariation.toFixed(1)}%) - some students need more support`
        });
    }
    
    return insights;
}

// Export functions
window.AnalyticsDashboard = {
    initializeAnalytics,
    refreshAnalytics,
    exportChart,
    calculateEngagementMetrics,
    generateInsights
};

// Auto-initialize if data is already available
document.addEventListener('DOMContentLoaded', function() {
    if (window.analyticsData) {
        initializeAnalytics(window.analyticsData);
    }
});

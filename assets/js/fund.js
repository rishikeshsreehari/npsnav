let navChart;
const parsedData = navData.map(item => {
    const [month, day, year] = item.date.split('/');
    return {
        x: new Date(year, month - 1, day),
        y: parseFloat(item.nav)
    };
}).sort((a, b) => a.x - b.x);

function initChart() {
    if (parsedData.length > 0) {
        const ctx = document.getElementById('navChart').getContext('2d');
        navChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'NAV',
                    data: parsedData,
                    borderColor: '#333',
                    backgroundColor: 'rgba(51, 51, 51, 0.1)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: {
                                day: 'MMM d',
                                month: 'MMM yyyy',
                                year: 'yyyy'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'NAV'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].raw.x.toLocaleDateString();
                            }
                        }
                    }
                }
            }
        });
    } else {
        console.error('No valid data to display in the chart');
        document.getElementById('navChart').innerHTML = 'No data available for chart';
    }
}

function getTimeUnit(range) {
    switch(range) {
        case '1M':
        case '3M':
            return 'day';
        case '6M':
        case '1Y':
            return 'month';
        case '3Y':
        case '5Y':
        case 'ALL':
            return 'year';
        default:
            return 'month';
    }
}

function filterData(range) {
    const currentDate = new Date();
    let startDate;

    switch(range) {
        case '1M':
            startDate = new Date(currentDate.setMonth(currentDate.getMonth() - 1));
            break;
        case '3M':
            startDate = new Date(currentDate.setMonth(currentDate.getMonth() - 3));
            break;
        case '6M':
            startDate = new Date(currentDate.setMonth(currentDate.getMonth() - 6));
            break;
        case '1Y':
            startDate = new Date(currentDate.setFullYear(currentDate.getFullYear() - 1));
            break;
        case '3Y':
            startDate = new Date(currentDate.setFullYear(currentDate.getFullYear() - 3));
            break;
        case '5Y':
            startDate = new Date(currentDate.setFullYear(currentDate.getFullYear() - 5));
            break;
        case 'ALL':
        default:
            startDate = new Date(0); // Beginning of time
    }

    const filteredData = parsedData.filter(item => item.x >= startDate);
    navChart.data.datasets[0].data = filteredData;
    
    // Update x-axis time unit
    const timeUnit = getTimeUnit(range);
    navChart.options.scales.x.time.unit = timeUnit;
    
    navChart.update();

    // Update return display
    const navReturnElement = document.getElementById('navReturn');
    if (range in returns && returns[range] !== 'NAN' && returns[range] !== '') {
        const returnValue = parseFloat(returns[range]);
        navReturnElement.textContent = `(${returnValue >= 0 ? '+' : ''}${returnValue}%)`;
        navReturnElement.classList.remove('positive', 'negative');
        navReturnElement.classList.add(returnValue >= 0 ? 'positive' : 'negative');
    } else {
        navReturnElement.textContent = '';
    }

    // Update active button state
    document.querySelectorAll('.timeframe-buttons button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`.timeframe-buttons button[onclick="filterData('${range}')"]`).classList.add('active');
}

// Initialize chart and show 1Y data by default
window.addEventListener('load', function() {
    initChart();
    filterData('1Y');
    window.scrollTo(0, 0);
});
let navChart;
const parsedData = navData.map(item => {
    const [month, day, year] = item.date.split('/');
    return {
        x: new Date(year, month - 1, day),
        y: parseFloat(item.nav),
        dateStr: item.date
    };
}).sort((a, b) => a.x - b.x);

// Parse Nifty data
const parsedNiftyData = niftyData.map(item => {
    const [month, day, year] = item.date.split('/');
    return {
        x: new Date(year, month - 1, day),
        y: parseFloat(item.nav),
        dateStr: item.date
    };
}).sort((a, b) => a.x - b.x);

// Function to get matching dates between fund and nifty data
function getMatchingData(fundData, niftyData) {
    const fundDateMap = new Map();
    const niftyDateMap = new Map();
    
    // Create maps for quick lookup
    fundData.forEach(item => {
        fundDateMap.set(item.dateStr, item);
    });
    
    niftyData.forEach(item => {
        niftyDateMap.set(item.dateStr, item);
    });
    
    // Find common dates
    const commonDates = [...fundDateMap.keys()].filter(date => niftyDateMap.has(date));
    
    const matchedFundData = commonDates.map(date => fundDateMap.get(date)).sort((a, b) => a.x - b.x);
    const matchedNiftyData = commonDates.map(date => niftyDateMap.get(date)).sort((a, b) => a.x - b.x);
    
    return { fundData: matchedFundData, niftyData: matchedNiftyData };
}

// Function to normalize data for comparison (base 100)
function normalizeData(data, baseValue = null) {
    if (data.length === 0) return [];
    
    const base = baseValue || data[0].y;
    return data.map(item => ({
        x: item.x,
        y: (item.y / base) * 100,
        dateStr: item.dateStr,
        originalValue: item.y
    }));
}

function formatINR(amount) {
    return new Intl.NumberFormat('en-IN').format(amount);
}

// Function to update investment comparison with table format
// Function to update investment comparison with table format
function updateInvestmentComparison(matchedFundData, matchedNiftyData, selectedRange) {
    const comparisonElement = document.getElementById('investmentComparison');
    if (!comparisonElement || matchedFundData.length === 0) return;
    
    const periods = ['1M', '3M', '6M', '1Y', '3Y', '5Y', 'ALL'];
    let tableHtml = '<div class="investment-returns">';
    tableHtml += '<h4>NPS vs Nifty Returns for a ₹10,000 Investment</h4>';
    tableHtml += `
        <div class="table-wrapper">
            <table class="returns-table">
                <thead>
                    <tr>
                        <th class="text-left">Period</th>
                        <th class="text-right">Invested On</th>
                        <th class="text-right">Fund Value</th>
                        <th class="text-right">Nifty Value</th>
                        <th class="text-right">Fund Returns</th>
                        <th class="text-right">Nifty Returns</th>
                        <th class="text-right">Annualised Fund Returns</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    periods.forEach(period => {
        // Use pre-calculated returns for consistency with main site
        const preCalculatedFundReturn = returns[period];
        
        if (period === 'ALL' || !preCalculatedFundReturn || preCalculatedFundReturn === '' || isNaN(parseFloat(preCalculatedFundReturn))) {
            // For ALL period or missing data, calculate from available data
            const currentDate = new Date();
            let startDate = period === 'ALL' ? new Date(0) : getStartDateForPeriod(period, currentDate);
            
            const filteredFundData = parsedData.filter(item => item.x >= startDate);
            const filteredNiftyData = parsedNiftyData.filter(item => item.x >= startDate);
            const { fundData: periodMatchedFundData, niftyData: periodMatchedNiftyData } = getMatchingData(filteredFundData, filteredNiftyData);
            
            if (periodMatchedFundData.length > 0) {
                const fundStartValue = periodMatchedFundData[0].y;
                const fundEndValue = periodMatchedFundData[periodMatchedFundData.length - 1].y;
                const niftyStartValue = periodMatchedNiftyData[0].y;
                const niftyEndValue = periodMatchedNiftyData[periodMatchedNiftyData.length - 1].y;
                
                const fundReturn = ((fundEndValue - fundStartValue) / fundStartValue) * 100;
                const niftyReturn = ((niftyEndValue - niftyStartValue) / niftyStartValue) * 100;
                
                // Calculate years for annualized return
                const startDateTime = periodMatchedFundData[0].x;
                const endDateTime = periodMatchedFundData[periodMatchedFundData.length - 1].x;
                const yearsInPeriod = (endDateTime - startDateTime) / (365.25 * 24 * 60 * 60 * 1000);
                
                let annualizedFundReturn;
                if (yearsInPeriod >= 1) {
                    annualizedFundReturn = (Math.pow((fundEndValue / fundStartValue), (1 / yearsInPeriod)) - 1) * 100;
                } else {
                    annualizedFundReturn = fundReturn;
                }
                
                const fundValue = Math.round(10000 * (1 + fundReturn / 100));
                const niftyValue = Math.round(10000 * (1 + niftyReturn / 100));
                
                const investedOnDate = periodMatchedFundData[0].x.toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: 'short',
                    year: '2-digit'
                });
                
                tableHtml += `
                    <tr>
                        <td class="period-cell text-left">${period}</td>
                        <td class="date-cell text-right">${investedOnDate}</td>
                        <td class="value-cell text-right">₹${formatINR(fundValue)}</td>
                        <td class="value-cell text-right">₹${formatINR(niftyValue)}</td>
                        <td class="return-cell text-right ${fundReturn >= 0 ? 'positive' : 'negative'}">${fundReturn >= 0 ? '+' : ''}${fundReturn.toFixed(2)}%</td>
                        <td class="return-cell text-right ${niftyReturn >= 0 ? 'positive' : 'negative'}">${niftyReturn >= 0 ? '+' : ''}${niftyReturn.toFixed(2)}%</td>
                        <td class="return-cell text-right ${annualizedFundReturn >= 0 ? 'positive' : 'negative'}">${annualizedFundReturn >= 0 ? '+' : ''}${annualizedFundReturn.toFixed(2)}%</td>
                    </tr>
                `;
            } else {
                tableHtml += `
                    <tr>
                        <td class="period-cell text-left">${period}</td>
                        <td colspan="6" class="no-data text-center">Insufficient data</td>
                    </tr>
                `;
            }
        } else {
            // Use pre-calculated returns from calculate.py for accuracy
            const fundReturn = parseFloat(preCalculatedFundReturn);
            
            // Calculate corresponding Nifty return for the same period
            const currentDate = new Date();
            const startDate = getStartDateForPeriod(period, currentDate);
            const filteredNiftyData = parsedNiftyData.filter(item => item.x >= startDate);
            
            let niftyReturn = 0;
            let investedOnDate = 'N/A';
            
            if (filteredNiftyData.length > 0) {
                const niftyStartValue = filteredNiftyData[0].y;
                const niftyEndValue = filteredNiftyData[filteredNiftyData.length - 1].y;
                niftyReturn = ((niftyEndValue - niftyStartValue) / niftyStartValue) * 100;
                
                investedOnDate = filteredNiftyData[0].x.toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: 'short',
                    year: '2-digit'
                });
            }
            
            const fundValue = Math.round(10000 * (1 + fundReturn / 100));
            const niftyValue = Math.round(10000 * (1 + niftyReturn / 100));
            
            // For annualized return, use the same logic as calculate.py
            let annualizedFundReturn;
            if (period === '3Y' || period === '5Y') {
                annualizedFundReturn = fundReturn; // Already annualized in calculate.py
            } else {
                annualizedFundReturn = fundReturn; // For shorter periods, same as absolute return
            }
            
            tableHtml += `
                <tr>
                    <td class="period-cell text-left">${period}</td>
                    <td class="date-cell text-right">${investedOnDate}</td>
                    <td class="value-cell text-right">₹${formatINR(fundValue)}</td>
                    <td class="value-cell text-right">₹${formatINR(niftyValue)}</td>
                    <td class="return-cell text-right ${fundReturn >= 0 ? 'positive' : 'negative'}">${fundReturn >= 0 ? '+' : ''}${fundReturn.toFixed(2)}%</td>
                    <td class="return-cell text-right ${niftyReturn >= 0 ? 'positive' : 'negative'}">${niftyReturn >= 0 ? '+' : ''}${niftyReturn.toFixed(2)}%</td>
                    <td class="return-cell text-right ${annualizedFundReturn >= 0 ? 'positive' : 'negative'}">${annualizedFundReturn >= 0 ? '+' : ''}${annualizedFundReturn.toFixed(2)}%</td>
                </tr>
            `;
        }
    });
    
    tableHtml += '</tbody></table></div></div>';
    comparisonElement.innerHTML = tableHtml;
}

// Helper function to get start date for a given period
function getStartDateForPeriod(period, currentDate) {
    switch(period) {
        case '1M':
            return new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, currentDate.getDate());
        case '3M':
            return new Date(currentDate.getFullYear(), currentDate.getMonth() - 3, currentDate.getDate());
        case '6M':
            return new Date(currentDate.getFullYear(), currentDate.getMonth() - 6, currentDate.getDate());
        case '1Y':
            return new Date(currentDate.getFullYear() - 1, currentDate.getMonth(), currentDate.getDate());
        case '3Y':
            return new Date(currentDate.getFullYear() - 3, currentDate.getMonth(), currentDate.getDate());
        case '5Y':
            return new Date(currentDate.getFullYear() - 5, currentDate.getMonth(), currentDate.getDate());
        default:
            return new Date(0);
    }
}

// Function to update methodology and disclaimer
function updateMethodologyAndDisclaimer(startDate, endDate) {
    const methodologyElement = document.getElementById('methodology');
    if (methodologyElement) {
        methodologyElement.innerHTML = `
            <div class="methodology-disclaimer">
                <p>The graph assumes normalized performance comparison starting from base value of 100 for both fund and Nifty 50 on ${startDate}. Subsequent values show relative performance with only matching dates present in both datasets included for fair comparison. Returns table shows hypothetical investment of ₹10,000 on the respective start dates. This represents unrealized gains/losses and past performance does not guarantee future results. Actual returns may vary due to fees, taxes, expense ratios, and market timing. This comparison assumes lump sum investment and does not account for dividends, distributions, or reinvestment. Nifty 50 returns are for illustration purposes only and do not represent actual investment options available to investors. Please consult with a qualified financial advisor before making investment decisions.</p>
            </div>
        `;
    }
}

function initChart() {
    if (parsedData.length > 0) {
        const ctx = document.getElementById('navChart').getContext('2d');
        
        // Get matching data for both datasets
        const { fundData: matchedFundData, niftyData: matchedNiftyData } = getMatchingData(parsedData, parsedNiftyData);
        
        // Normalize both datasets to start at 100 for comparison
        const normalizedFundData = normalizeData(matchedFundData);
        const normalizedNiftyData = normalizeData(matchedNiftyData);
        
        navChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Fund NAV',
                    data: normalizedFundData,
                    borderColor: '#000000',
                    backgroundColor: 'rgba(0, 0, 0, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    yAxisID: 'y'
                }, {
                    label: 'Nifty 50',
                    data: normalizedNiftyData,
                    borderColor: '#666666',
                    backgroundColor: 'rgba(102, 102, 102, 0.1)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                    borderDash: [5, 5],
                    yAxisID: 'y'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
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
                            text: 'Normalized Value (Base 100)'
                        },
                        beginAtZero: false
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(tooltipItems) {
                                return tooltipItems[0].raw.x.toLocaleDateString();
                            },
                            label: function(context) {
                                const originalValue = context.raw.originalValue;
                                const normalizedValue = context.parsed.y.toFixed(2);
                                if (context.dataset.label === 'Fund NAV') {
                                    return `${context.dataset.label}: ₹${originalValue} (Normalized: ${normalizedValue})`;
                                } else {
                                    return `${context.dataset.label}: ${originalValue} (Normalized: ${normalizedValue})`;
                                }
                            }
                        }
                    }
                }
            }
        });

        const firstDate = new Date(Math.min(...parsedData.map(item => item.x)));
        const lastDate = new Date(Math.max(...parsedData.map(item => item.x)));
        const currentDate = new Date();
        
        const buttonsToHide = [];

        ['1M', '3M', '6M', '1Y', '3Y', '5Y'].forEach(range => {
            let shouldHide = false;
            
            const rangeInMonths = parseInt(range);
            const rangeStartDate = new Date(currentDate);
            rangeStartDate.setMonth(rangeStartDate.getMonth() - rangeInMonths);
            if (firstDate > rangeStartDate) {
                shouldHide = true;
            }
            
            if (!returns[range] || isNaN(parseFloat(returns[range])) || returns[range] === '') {
                shouldHide = true;
            }
            
            if (shouldHide) {
                buttonsToHide.push(range);
            }
        });

        hideButtons(buttonsToHide);
    } else {
        console.error('No valid data to display in the chart');
        document.getElementById('navChart').innerHTML = 'No data available for chart';
    }
}

function hideButtons(buttonsToHide) {
    document.querySelectorAll('.timeframe-buttons button').forEach(button => {
        if (buttonsToHide.includes(button.textContent) && button.textContent !== 'ALL') {
            button.style.display = 'none';
        } else {
            button.style.display = '';
        }
    });
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
            startDate = new Date(0);
    }

    // Filter both datasets to the selected time range
    const filteredFundData = parsedData.filter(item => item.x >= startDate);
    const filteredNiftyData = parsedNiftyData.filter(item => item.x >= startDate);
    
    // Get matching data for the filtered period
    const { fundData: matchedFundData, niftyData: matchedNiftyData } = getMatchingData(filteredFundData, filteredNiftyData);
    
    // Normalize the matched data
    const normalizedFundData = normalizeData(matchedFundData);
    const normalizedNiftyData = normalizeData(matchedNiftyData);
    
    // Update chart data
    navChart.data.datasets[0].data = normalizedFundData;
    navChart.data.datasets[1].data = normalizedNiftyData;
    
    // Update x-axis time unit
    const timeUnit = getTimeUnit(range);
    navChart.options.scales.x.time.unit = timeUnit;
    
    navChart.update();

    // Update methodology and disclaimer
    if (matchedFundData.length > 0) {
        const startDate = matchedFundData[0].x.toLocaleDateString();
        const endDate = matchedFundData[matchedFundData.length - 1].x.toLocaleDateString();
        updateMethodologyAndDisclaimer(startDate, endDate);
        updateInvestmentComparison(matchedFundData, matchedNiftyData, range);
    }

    // Update return display
    const navReturnElement = document.getElementById('navReturn');
    if (range !== 'ALL' && returns[range] && !isNaN(parseFloat(returns[range])) && returns[range] !== '') {
        const returnValue = parseFloat(returns[range]);
        navReturnElement.textContent = `${returnValue >= 0 ? '+' : ''}${returnValue}%`;
        navReturnElement.classList.remove('positive', 'negative');
        navReturnElement.classList.add(returnValue >= 0 ? 'positive' : 'negative');
    } else {
        navReturnElement.textContent = '';
    }

    // Update active button state
    document.querySelectorAll('.timeframe-buttons button').forEach(btn => {
        btn.classList.remove('active', 'selected');
    });
    const selectedButton = document.querySelector(`.timeframe-buttons button[onclick="filterData('${range}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active', 'selected');
    }
}

// Initialize chart and show data by default
window.addEventListener('load', function() {
    initChart();
    
    const buttons = document.querySelectorAll('.timeframe-buttons button');
    let defaultButton;
    for (let button of buttons) {
        if (button.style.display !== 'none') {
            defaultButton = button;
            break;
        }
    }
    
    if (document.querySelector('.timeframe-buttons button[onclick="filterData(\'1Y\')"]').style.display !== 'none') {
        filterData('1Y');
    } else if (defaultButton) {
        filterData(defaultButton.textContent);
    }
    
    window.scrollTo(0, 0);
});
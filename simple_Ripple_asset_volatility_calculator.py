#
# Ripple asset volatility calculator:
# - Query Ripple Data API for historical exchange rates
# - Calculate volatility (via standard deviation)
# - Output a plot of exchange rate and volatility
# Python 2.7
#
# iounewsblog@gmail.com
# @iounews
# tomxcs on https://www.xrpchat.com
# 2016-10-01
#

import requests
import datetime
from numpy import nanstd, array, arange
from matplotlib import pyplot

# Basic query info
apiUrl = 'https://data.ripple.com/v2/exchange_rates/' # Using Ripple Data API exchange_rates method
currency1 = 'XRP'
issuer1 = '' # If XRP, do not use an issuing wallet address
issuer1Name = ''
currency2 = 'USD'
issuer2 = 'rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B'
issuer2Name = 'Bitstamp'

# Date range for queries
endDate = datetime.datetime.utcnow() # Use UTC today for latest data
startDate = datetime.date(2013,4,1)

# Simple Ripple Data API query
def getPrice(baseUrl, cur1, iss1, cur2, iss2, methodParams):
    return requests.get(baseUrl + cur1 + '+' + iss1 + '/' + cur2 + '+' + iss2, params=methodParams)

# Generate range of dates to query
def dateRange(startDate, endDate):
    dates = []
    # Use ISO ordinal date for easy iteration
    startOrdinal = startDate.toordinal()
    endOrdinal = endDate.toordinal() + 1
    for dateOrdinal in range(startOrdinal, endOrdinal):
        dateISO = datetime.date.fromordinal(dateOrdinal).isoformat()
        dates.append(dateISO)
    return dates

#
# Calculate standard deviations of sliding windows of arbitrary size
# Use degFreedom = 0 for population, 1 for sample
#
def stDevPeriodWindow(values, size, degFreedom):
    # Pad arrays with leading 0.0s
    stDevValues = [0.0]*(size-1)
    normStDevValues = []
    for i in range(0, len(values)-size+1):
        # Create array with window's data
        periodValues = []
        periodValues = array(values[i:size+i], dtype=float)
        # Calculate standard deviation using function that ignores 'NaN'
        periodStDev = nanstd(periodValues, ddof=degFreedom)
        stDevValues.append(periodStDev)
    # Normalize standard deviations
    normStDevValues = map(lambda s, val: float(s) / float(val), stDevValues, values)
    return stDevValues, normStDevValues

# Create array of dates for exchange rate query.
dates = dateRange(startDate,endDate)

# Query for exchange rates and add to array
print('Querying ' + apiUrl + ' for ' + currency1 + '.' + issuer1 + '/' + currency2 + '.' + issuer2 + ' exchange rates...') 
prices = []
for date in dates:
    dateParams = {"date": date + "T00:00:00Z"}
    price = getPrice(apiUrl, currency1, issuer1, currency2, issuer2, dateParams)
    print('.'),
    #print(date + ',' + price.json()['rate'])
    # If exchange rate is 0.0, add NaN to array to avoid aberrations in volatility calculation
    if float(price.json()['rate']) == 0:
        prices.append('NaN')
    else:
        prices.append(price.json()['rate'])

# Make sure prices are floating point
pricesFloat = [float(x) for x in prices]

# Calculate volatility (as standard deviation)
priceVolatility, normPriceVolatility = stDevPeriodWindow(pricesFloat, 7, 1)

# Zipped arrays
volatilityData = zip(dates, pricesFloat, priceVolatility, normPriceVolatility)

# Create and print comma-delimited data
volatilityDataDelimited = "Date,Price,StDev_ddof=1,NormStDev_ddof=1\n"
for tup in volatilityData:
    volatilityDataDelimited += ','.join([str(x) for x in tup]) + '\n'
print(volatilityDataDelimited)

#
# Plotting
#

# Set up ticks on X-axis
# Ticks are spaced approx. every three months - not exact.
tickLocations = arange(0,len(dates),91.25)
xLabels = ["2013/04", "2013/07", "2013/10", "2014/01", "2014/04", "2014/07", "2014/10", "2015/01", "2015/04", "2015/07", "2015/10", "2016/01", "2016/04", "2016/07", "2016/10"]

# Set up plot figure
fig = pyplot.figure()
fig.suptitle(currency1 + '.' + issuer1Name + '/' + currency2 + '.' + issuer2Name + ' Volatility', fontsize=16)

# Plot price of currency1 in currency2
pricesPlot = pyplot.subplot(311)
pricesPlot.plot(pricesFloat, color='blue')
pyplot.ylabel(currency1 + '.' + issuer1Name + '/' + currency2 + '.' + issuer2Name)
pyplot.xticks(tickLocations, xLabels)
pyplot.setp(pricesPlot.get_xticklabels(), visible=False) # Hide X-axis labels

# Plot volatility
volPlot = pyplot.subplot(312, sharex=pricesPlot)
volPlot.plot(priceVolatility, color='red')
pyplot.ylabel('Volatility')
pyplot.setp(volPlot.get_xticklabels(), visible=False) # Hide X-axis labels

# Plot normalized volatility
normVolPlot = pyplot.subplot(313, sharex=pricesPlot)
pyplot.ylabel('Normalized\nVolatility')
pyplot.xlabel('Date')
normVolPlot.plot(normPriceVolatility, color='green')

# Display & save plot
pyplot.tight_layout()
# Automatically save figure to working directory
#pyplot.savefig("XRP_USDBitstamp-price_volatility_normvolatility.png")
pyplot.show()

###Twitter API and analysis below
import urllib.request, datetime, json, codecs, time
from io import StringIO
import numpy as np
import matplotlib.pyplot as plt

def getStockQuote(stock, date):        
    url_1="http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.historicaldata%20where%20symbol%20%3D%20"
    url_2='%20and%20startDate%20%3D%20'
    url_3='%20and%20endDate%20%3D%20'
    url_4="&format=json&diagnostics=true&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback="
    
    URL = url_1+'"'+stock+'"'+url_2+'"'+date+'"'+url_3+'"'+date+'"'+url_4
    rawData = urllib.request.urlopen(URL).read()
    data = json.loads(rawData.decode('utf-8'))
    if data['query']['results'] == None: #stock market closed so next day
        data, date = refineDate(URL, stock, data, date)
        
    if date == str(datetime.date.today()):
        return None
    else:
        Close = float(data['query']['results']['quote']['Close']) #access Json
        return Close


 
def refineDate(URL, stock, data, date):#works with get stock quote and date incrementer
    while data['query']['results'] == None: #keeps going until market open
        date = dateIncrementer(date)
        url_1="http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.historicaldata%20where%20symbol%20%3D%20"
        url_2='%20and%20startDate%20%3D%20'
        url_3='%20and%20endDate%20%3D%20'
        url_4='&format=json&diagnostics=true&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback='
        URL = url_1+'"'+stock+'"'+url_2+'"'+date+'"'+url_3+'"'+date+'"'+url_4
        rawData = urllib.request.urlopen(URL).read()
        data = json.loads(rawData.decode('utf-8'))
    return data, date


def dateIncrementer(date):
    today = str(datetime.date.today())
    today_parts = today.split('-')

    parts = date.split('-')
    day = int(parts[2])
    month = int(parts[1])
    year = int(parts[0])

    if date == str(today):
        return False #need to cancel function execution on this tweet
    elif month <= 7 and month%2==1 and day ==31:#first 6 months days in month
        month = month + 1
        date = parts[0] + '-' + '0' + str(month) + '-' + '01'
    elif month == 2 and year%4==0 and day ==28: #february
        day = day +1
        if day < 10:
            date = parts[0] + '-' + parts[1] + '-' +'0'+ str(day)
        else: 
            date = parts[0] + '-' + parts[1] + '-' + str(day)
    elif month == 2 and year%4==0 and day ==29:
        date = parts[0] + '-' + '03' + '-' + '01'
    elif month == 2 and year%4!=0 and day ==28:
        date = parts[0] + '-' + '03' + '-' + '01'
    elif month <=7 and month%2==0 and month!=2 and day ==30:
        month = month + 1
        date = parts[0] + '-' +'0' + str(month) + '-' + '01'    
    elif month>7 and month%2==0 and day ==31 and month!=12:
        month = month +1
        if month <10:
            date = parts[0] + '-' + '0' + str(month) + '-' + '01'    
        else: 
            date = parts[0] + '-' + str(month) + '-' + '01'
    elif month>7 and month%2==0 and day ==31 and month==12:
        date = parts[0] + '-' + '01' + '-' + '01'
    elif month>7 and month%2==1 and day==30:
        month = month +1
        if month <10:
            date = parts[0] + '-' +'0' + str(month) + '-' + '01'    
        else: 
            date = parts[0] + '-' + str(month) + '-' + '01'
    else: #none of the above edge cases
        day = day +1
        if day <10:
            date = parts[0] + '-' + parts[1] + '-' + '0' + str(day)    
        else: 
            date = parts[0] + '-' + parts[1] + '-' + str(day)
    return date

#dateIncrementer('2016-03-02')

def getEarnings(timePeriod): #time periods in terms of 
    yearOne = ['2016-04-26', '2016-07-26', '2016-10-25', '2017-01-31']
    yearTwo = ['2015-04-26', '2015-07-26', '2015-10-25', '2016-01-31']
    yearThree = ['2014-04-26', '2014-07-26', '2014-10-25', '2015-01-31']
    allYears = yearOne+yearTwo+yearThree
    quarters = int(4*timePeriod)
    return allYears[:quarters]

def nearbyDates(dates):#takes a list of dates
    dates_per_date = 5 #how many nearby days?
    moreDates = []
    for date in dates:
        for i in range(dates_per_date):
            moreDates.append(date)
            date = dateIncrementer(date)
    return moreDates


def getEarningsTrends(stock, timePeriod):
    earnings_dates = getEarnings(timePeriod) #returns a list of earnings dates
    dates_to_consider = nearbyDates(earnings_dates)
    #multiplies dates for accuracy
    
    prices = []
    for date in dates_to_consider:
        prices.append(getStockQuote(stock, date))
    
    return prices, dates_to_consider


def plotPrices(xvals, yvals):
    #xvals = range(len(xvals))
    pattern = '%Y-%m-%d'
    for i in range(len(xvals)):
        xvals[i] = int(time.mktime(time.strptime(xvals[i], pattern)))
    margin = 10
    plt.axis([min(xvals), max(xvals)+2, 0, max(yvals)+margin])
    #slope, intercept = np.polyfit(xvals, yvals, 1)
    #abline_values = [slope * i + intercept for i in xvals]
    plt.plot(xvals, yvals, '--')
    #plt.plot(xvals, abline_values, 'b')
    #plt.title(slope)
    plt.show()


def main(stock, timePeriod):
    #main function that will collect relevant stock prices and plot them
    prices, dates = getEarningsTrends(stock, timePeriod)
    print(prices, dates)
    plotPrices(dates, prices)
    
main('fb', 1)
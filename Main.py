import os
from flask import Flask
from flask import render_template, request
from wtforms import Form, BooleanField, TextField, PasswordField, validators

app = Flask(__name__)
###Twitter analysis code below
import string, os, datetime
import numpy as np
import matplotlib.pyplot as plt#, mpld3
from matplotlib import animation
from matplotlib.animation import FuncAnimation
from matplotlib import style
import twitter
from GetOldTweets import got3

#style.use('fivethirtyeight')

consumer_key='LZedcCMbUoRRMtkfNnF9jqXQC'
consumer_secret='EjY60p2nqxbHRqwdbSkr68HbGIMXeWhYR81BYkuaKlkM0VCoL4'
oauth_token='517112590-a0bWwypsSspHT9L6sT1jhK2ifKYLW7CufWCZryOD'
oauth_token_secret='BtQwOg7UyxS9RO8zmIHdInwScy9ehBspZs0D6lJYYjpCx'

api = twitter.Api(consumer_key='LZedcCMbUoRRMtkfNnF9jqXQC',
    consumer_secret='EjY60p2nqxbHRqwdbSkr68HbGIMXeWhYR81BYkuaKlkM0VCoL4',
    access_token_key='517112590-a0bWwypsSspHT9L6sT1jhK2ifKYLW7CufWCZryOD',
    access_token_secret='BtQwOg7UyxS9RO8zmIHdInwScy9ehBspZs0D6lJYYjpCx')
    
class StockForm(Form):
    stock = TextField('Enter a Valid Stock Ticker:', [validators.Length(min=2, max=140)])
    time = TextField('Enter a Time Period: ie 0.5, 1 or 2 years')


## Working with Twitter API 
## Making use of getoldtweets repo mentioned in citations: https://github.com/Jefferson-Henrique/
def getTweets(rawStock, dates):
    stock = '$' #seach symbol for stocks on twitter
    for letter in rawStock:
        if letter in string.ascii_letters:
            letter = letter.upper() #standardize stock to uppercase
            stock = stock + letter
            
    tweets = dict()
    def testDate(day):
        try:
            tweetCriteria = got3.manager.TweetCriteria().setQuerySearch(stock).setSince(day).setUntil(dateIncrementer(day)).setMaxTweets(4)
            if got3.manager.TweetManager.getTweets(tweetCriteria) != []: 
                return True 
        except: 
            return False
    
    dates = list(filter(testDate, dates))
    for day in dates:
        tweetCriteria = got3.manager.TweetCriteria().setQuerySearch(stock).setSince(day).setUntil(dateIncrementer(day)).setMaxTweets(4)
        tweets[day] = extractTweets(tweetCriteria) #add a set of tweets to the dictionary of days
    return tweets, dates


def extractTweets(tweetData):
    tweets = set()
    for tweet in got3.manager.TweetManager.getTweets(tweetData):
        tweets.add(tweet.text)
    return tweets
    
    
def getMonthlyDates(date):
    days = ['02', '07', '12', '17', '22'] #dates spread throughout month
    monthly_dates = []                    #all less than 27 becuase february
    for day in days:
        monthly_dates.append(date+day)
    return monthly_dates


def backMonths(num_of_months, date):
    date_parts = date.split('-')
    years=(num_of_months-int(date_parts[1]))//12
    if num_of_months>=int(date_parts[1]):
        date_parts[0]=str(int(date_parts[0])-1-years)
    month = (int(date_parts[1])-num_of_months)%12
    if month==0:
        month=12
    if month<10:
        month = '0'+ str(month)
    else:
        month = str(month)
    return date_parts[0]+'-'+month+'-'
    
    
def getDates(timePeriod):
    today = str(datetime.date.today())
    year = 12
    months = int(timePeriod*year) #based on my definition of timePeriod
    dates = []
    
    for i in range(1, months+1):
        date = backMonths(i, today) #gives only yyyy-mm- and add days
        dates.extend(getMonthlyDates(date))
        
    return dates
    
    
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


##  Sentiment Analysis Code

def getTweetSentiments(stock, timePeriod):
    #gets overall trend in sentiment towards the company
    #start from previous month and go back as far as necessary
    dates = getDates(timePeriod)

    tweets_of_days, dates = getTweets(stock, dates)
    tweetsToShow = set()
    sentiments = []
    for tweets in tweets_of_days:
        sentiments.append(evaluateSenti(tweets_of_days[tweets], tweetsToShow))
    return sentiments, dates, tweetsToShow


def evaluateSenti(tweets, tweetsToShow):
    score = 0
    for tweet in tweets:
        score += evaluate(tweet, tweetsToShow)
    return score/len(tweets)


#creates dictionary for bag of words approach
vals = dict()
#uses polarity values from AFINN mentioned in citations: http://www2.imm.dtu.dk/pubdb/views/publication_details.php?id=6010
#worked with this file before but had to implement new version of senti analysis as old code becuase python 3 not 2
file = open('polarity.txt' , encoding='utf-8')
infile = file.read()
infile=infile.splitlines()
for x in infile:
    x = x.strip()
    pieces = x.split(" ") #breaks down the polarity file into pieces
    vals[str(pieces[0])] = int(pieces[1])  #goes through all polarities and indexing them in value[]



def evaluate(tweet, tweetsToShow):
    pos, neg = 0.00, 0.00
    words = tweet.split(" ") #indexes each word into a list
    num_pos, num_neg = 0, 0

    for w in words:
        w = w.lower() #makes it all uniform

        if w in vals:  #if any of the words in this index have a polarization value
            if vals[w]>0:  #record the polarization value
                pos += vals[w]
                num_pos += 1
            else:
                neg += abs(vals[w])
                num_neg += 1
    #below is to avoid zerodivision error
    if int(num_neg) == 0 and int(num_pos) == 0:
            net = 0
    elif int(num_neg) == 0:
        net = pos/num_pos
    elif int(num_pos) ==0:
        net = -(neg/num_neg)
    else:
        net = (pos/num_pos) - (neg/num_neg)
    total = (net/5)
    if num_neg+num_pos>2:
        tweetsToShow.add(tuple(makeTweetDisplayable(tweet, words)))
    return total


def makeTweetDisplayable(tweet, words):
    sentiPerWord = [] #stores if each word is positive or negative
    #using the color associated with that emotion
    for w in words:
        w=w.lower()
        if w in vals:
            if vals[w]>0: #higher threshold value for displaying
                sentiPerWord.append('g')
            elif vals[w]<0:
                sentiPerWord.append('r')
            else:
                sentiPerWord.append('b')
        else: sentiPerWord.append('b')
    sentiPerWord = tuple(sentiPerWord)
    return tweet, sentiPerWord



### Yahoo finance api used below
import urllib.request, json, codecs, time
from io import StringIO

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


### Main Function

def verifyStock(stock):
    url_1="http://query.yahooapis.com/v1/public/yql?q=select%20*%20from%20yahoo.finance.historicaldata%20where%20symbol%20%3D%20"
    url_2='%20and%20startDate%20%3D%20'
    url_3='%20and%20endDate%20%3D%20'
    url_4="&format=json&diagnostics=true&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback="
    date='2017-02-03'
    URL = url_1+'"'+stock+'"'+url_2+'"'+date+'"'+url_3+'"'+date+'"'+url_4
    rawData = urllib.request.urlopen(URL).read()
    data = json.loads(rawData.decode('utf-8'))
    if data['query']['results']==None:
        return False
    return True


#bootstrap was used for templates: https://startbootstrap.com/template-categories/all/
@app.route('/', methods = ['GET','POST'])
def main():
    global tweetsToShow
    form = StockForm(request.form)
    if request.method == 'POST':
        stock = str(form.stock.data)
        stock=stock.lower()
        check = verifyStock(stock)
        print(check)
        if not check:
            return render_template('main.html', form=form)
            
        timePeriod = float(form.time.data) #decimal of months out of a year
        if timePeriod not in [0.5, 1, 1.5, 2, 2.5, 3]:
            return render_template('main.html', form=form)
        
        prices, dates1 = getEarningsTrends(stock, timePeriod)
        #give a plotable set of 2 lists
        print("pre golobal dec")
        sentiments, dates2, tweetsToShow = getTweetSentiments(stock, timePeriod)
        average_senti=round(sum(sentiments)/len(sentiments), 2)
        print("post global dec")
        quartPrice = prices[0]/4
        for i in range(len(sentiments)):
            sentiments[i] = sentiments[i]*quartPrice + (3*quartPrice)
        #want to plot sentiments relative to each other to find trends
        #so set sentiment 0 to middle point on stock chart (max of prices/2)
        #plot points (middle point)+(middle*sentiment)
        linearCoeffs1, linearCoeffs2, polyCoeffs1, polyCoeffs2 = plotValues(dates1, prices, dates2, sentiments)
        #both plots and returns regressions for later use
        stock = stock.upper()
        plt.savefig("/Users/Tegjeev/Desktop/TermProject/TP1/static/chart.png")
        
        short_term, long_term = recomender(dates1, prices, dates2, sentiments, linearCoeffs1, linearCoeffs2, polyCoeffs1, polyCoeffs2)
        if short_term:
            short_term='Buy'
        else:
            short_term='Sell'
        if long_term:
            long_term = 'Buy'
        else:
            long_term='Sell'
        recent_price=round(prices[len(prices)-1], 2) #most recent price used
        print("good to go")
        return render_template('show.html', short_term=short_term, long_term=long_term, average_senti=average_senti, price=recent_price)
    return render_template('main.html', form=form)




### Regression and plotting code below
def plotValues(xvals1, yvals1, xvals2, yvals2): #all plotting occurs in this function
    xvals1 = makeDatesInts(xvals1)
    xvals2 = makeDatesInts(xvals2)
    fig, axarr = plt.subplots(2, 2)
    axarr[0, 0].axis([min(xvals1), max(xvals1), 0, max(yvals1)+yvals1[0]/8])
    axarr[0, 0].plot(xvals1, yvals1, 'x')
    axarr[0, 0].set_title('Prices Linear')
    axarr[0, 1].axis([min(xvals2), max(xvals2), 0, max(yvals2)+yvals2[0]/8])
    axarr[0, 1].plot(xvals2, yvals2)
    axarr[0, 1].set_title('Sentiment Linear')
    axarr[1, 0].axis([min(xvals1), max(xvals1), 0, max(yvals1)+yvals1[0]/8])
    axarr[1, 0].plot(xvals1, yvals1, 'x')
    axarr[1, 0].set_title('Prices Polynomial')
    axarr[1, 1].axis([min(xvals2), max(xvals2), 0, max(yvals2)+yvals2[0]/8])
    axarr[1, 1].plot(xvals2, yvals2)
    axarr[1, 1].set_title('Sentiment Polynomial')
    # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
    plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
    plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        
    #below finds all regressions
    slope1, intercept1 = findRegressionLinear(xvals1, yvals1)
    slope2, intercept2 = findRegressionLinear(xvals2, yvals2)
    
    a01, a11, a21, a31 = findRegressionPoly(xvals1, yvals1)
    a02, a12, a22, a32 = findRegressionPoly(xvals2, yvals2)
    
    #below plots regression
    abline_values1 = [slope1 * i + intercept1 for i in xvals1]
    axarr[0, 0].plot(xvals1, abline_values1, 'b')
    abline_values2 = [slope2 * i + intercept2 for i in xvals2]
    axarr[0, 1].plot(xvals2, abline_values2, 'r')
    
    cubic_values1 = [(a01*(i**3))+(a11*(i**2))+(a21*i)+a31 for i in xvals1]
    axarr[1, 0].plot(xvals1, cubic_values1, label="deg=3")
    
    cubic_values2 = [(a02*(i**3))+(a12*(i**2))+(a22*i)+a32 for i in xvals2]
    axarr[1, 1].plot(xvals2, cubic_values2, label="deg=3")
    
    return (slope1, intercept1), (slope2, intercept2), (a01, a11, a21, a31), (a02, a12, a22, a32)#for later use
    
    

def makeDatesInts(dates):
    pattern = '%Y-%m-%d'
    for i in range(len(dates)):
        dates[i] = (int(time.mktime(time.strptime(dates[i], pattern)))/10000000)-140 #fixed val dangerous
    return dates
    

#gradient descent theory learned from http://machinelearningmastery.com/gradient-descent-for-machine-learning/

def gradStepLinear(xvals, yvals, b, m, learning_rate):
    #use least squares equation to establish relationship between b, m and error
    #Take partial derivative of least squares equation to 'guide' m and b values
    #Guides error to optimal level with m and b
    #keep adding grad per iteration until adding 0 (at optimal point)
    b_gradient = 0 
    m_gradient = 0
    N = len(xvals) #number of data points
    for point in range(N):
        b_gradient += (-2/N)*(yvals[point]-((m*xvals[point])+b))
        m_gradient += (-2/N)*xvals[point]*(yvals[point]-((m*xvals[point])+b))
        #these are the partial derivatives of the error function
        #sum them over all points
    new_b = b - (learning_rate*b_gradient) #gives small step euler style
    new_m = m - (learning_rate*m_gradient)
    return new_b, new_m
    

def findRegressionLinear(xvals, yvals): #should output a gradient and y intercept
    learning_rate = 0.00001
    b = 0
    m = 0
    iterations = 100000 #change if necessary for more data points
    
    for i in range(iterations):
        b, m = gradStepLinear(xvals, yvals, b, m, learning_rate)
    return m, b


def findRegressionPoly(xvals, yvals): #should output a cubic polynomial
    learning_rate = 0.0000001
    a0, a1, a2, a3 = 0, 0, 0, 0
    iterations = 100000 #change if necessary for more data points
    
    for i in range(iterations):
        a0, a1, a2, a3 = gradStepPoly(xvals, yvals, a0, a1, a2, a3, learning_rate)
    return a0, a1, a2, a3


def gradStepPoly(xvals, yvals, a0, a1, a2, a3, learning_rate):
    #use least squares equation to establish relationship
    #Partial derivatives of least squares equation 'guide' coefficient vals
    #Keep adding grad per iteration until adding 0 (at optimal point)
    a0_gradient = 0 
    a1_gradient = 0
    a2_gradient = 0
    a3_gradient = 0
    
    N = len(xvals) #number of data points
    
    for point in range(N):
        a0_gradient += (-2/N)*(xvals[point]**3)*(yvals[point]-(a0*xvals[point]**3+a1*xvals[point]**2+a2*xvals[point]+a3))
        a1_gradient += (-2/N)*(xvals[point]**2)*(yvals[point]-(a0*xvals[point]**3+a1*xvals[point]**2+a2*xvals[point]+a3))
        a2_gradient += (-2/N)*(xvals[point]**1)*(yvals[point]-(a0*xvals[point]**3+a1*xvals[point]**2+a2*xvals[point]+a3))
        a0_gradient += (-2/N)*(yvals[point]-(a0*xvals[point]**3+a1*xvals[point]**2+a2*xvals[point]+a3))
        #these are the partial derivatives of the error function
        #sum them over all points
    new_a0 = a0 - (learning_rate*a0_gradient) #gives small step euler style
    new_a1 = a1 - (learning_rate*a1_gradient)
    new_a2 = a2 - (learning_rate*a2_gradient)
    new_a3 = a3 - (learning_rate*a3_gradient)
    return new_a0, new_a1, new_a2, new_a3

###Make animation - make animation by recreating the optimization


def makeLinearSubplots(xvals, yvals, title, updates): #do it for each plot one at a time
    fig, ax = plt.subplots() #creates all subplots in plt
    #plot data points per plot
    ax.plot(xvals, yvals, 'x')
    ax.set_title(title)
    line, = ax.plot(xvals, [updates[1][0]*x+updates[1][1] for x in xvals], 'r-', linewidth=2)
    
    def updateLinear(frame):
        line.set_ydata([updates[frame][0]*x + updates[frame][1] for x in xvals]) #frames is a list of coefficients
        return line
        
    anim = FuncAnimation(fig, updateLinear, frames=np.arange(1, 10), interval=200)
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)
    
    anim.save(title+'.mp4', writer='imagemagick')
    plt.clf() #ready for next plot



###Recomender Code Below

def recomender(xvals1, yvals1, xvals2, yvals2, linearCoeffs1, linearCoeffs2, polyCoeffs1, polyCoeffs2):    
    sqeLinear1 = getSquaredError(line, xvals1, yvals1, linearCoeffs1)
    sqeLinear2 = getSquaredError(line, xvals2, yvals2, linearCoeffs2)
    sqePoly1 = getSquaredError(poly, xvals1, yvals1, polyCoeffs1)
    sqePoly2 = getSquaredError(poly, xvals2, yvals2, polyCoeffs2)
    
    total = sqeLinear1 + sqeLinear2 + sqePoly1 + sqePoly2
    w1, w2 = getW(total, sqeLinear1), getW(total, sqeLinear2)
    w3, w4 = getW(total, sqePoly1), getW(total, sqePoly2)
    
    date1 = '2017-02-02'
    date2 = '2017-02-03'
    
    dates = makeDatesInts([date1, date2])
    oneDay = dates[1]-dates[0]
    
    shortTerm = 30
    longTerm = 120
    
    shortTermIntVal = shortTerm*oneDay
    longTermIntVal = longTerm*oneDay
    
    X1Max = max(xvals1)
    X2Max = max(xvals2)
    
    sForward_linePrice1 = line(linearCoeffs1, X1Max+shortTermIntVal)
    sForward_linePrice2 = line(linearCoeffs2, X2Max+shortTermIntVal)
    sForward_polyPrice1 = poly(polyCoeffs1, X1Max+shortTermIntVal)
    sForward_polyPrice2 = poly(polyCoeffs2, X2Max+shortTermIntVal)
    
    current1 = yvals1[xvals1.index(X1Max)]
    current2 = yvals2[xvals2.index(X2Max)]
    
    line_delta1 = sForward_linePrice1 - current1
    line_delta2 = sForward_linePrice2 - current2
    poly_delta1 = sForward_polyPrice1 - current1
    poly_delta2 = sForward_polyPrice2 - current2
    
    total_deltaShortTerm = line_delta1*w1 + line_delta2*w2 + poly_delta1*w3 + poly_delta2*w4
    
    if total_deltaShortTerm+current1>current1:
        buy_short = True
    else:
        buy_short = False
    
    lForward_linePrice1 = line(linearCoeffs1, X1Max+longTermIntVal)
    lForward_linePrice2 = line(linearCoeffs2, X2Max+longTermIntVal)
    lForward_polyPrice1 = poly(polyCoeffs1, X1Max+longTermIntVal)
    lForward_polyPrice2 = poly(polyCoeffs2, X2Max+longTermIntVal)
    
    line_delta1 = lForward_linePrice1 - current1
    line_delta2 = lForward_linePrice2 - current2
    poly_delta1 = lForward_polyPrice1 - current1
    poly_delta2 = lForward_polyPrice2 - current2
    
    total_deltaLongTerm = line_delta1*w1 + line_delta2*w2 + poly_delta1*w3 + poly_delta2*w4
    
    if total_deltaLongTerm+current1>1.15*current1:
        buy_long = True
    else: buy_long = False
    
    return (buy_short, buy_long)

    
def getW(total, sqe): #weights smaller ones the highest
    return (total-sqe)/(3*total)
    
    
def line(coeffs, x): #coeff format (m, b)
    return coeffs[0]*x + coeffs[1]
    

def poly(coeffs, x): #coeffs in format (a0, a1, a2, a3)
    return coeffs[0]*(x**3) + coeffs[1]*(x**2) + coeffs[2]*x + coeffs[1]
    

def getSquaredError(function, xvals, yvals, coeffs):
    totalError=0
    
    for point in range(len(xvals)):
        totalError += (yvals[point]-function(coeffs, xvals[point]))**2
    return totalError/len(xvals)


###Display tweets
@app.route('/sentiment/', methods = ['GET','POST'])
def displayTweets():
    
    tweets = tweetsToShow #each tweet given has at least 2 senti words
    counter = 0
    threeTweets = []
    
    for tweet in tweets:
        counter+=1
        threeTweets.append(tweet)
        if counter==3: break
    displayable = []
    
    for tweet in threeTweets:
        displayable.extend(getBreaks(tweet[0], tweet[1]))
    
    while len(displayable)<21:
        displayable.append('')
    
    return render_template('sentiment.html', T1black1=displayable[0], 
                            T1outlier1=displayable[1], T1color1=displayable[2],
                            T1black2=displayable[3], T1outlier2=displayable[4], 
                            T1color2=displayable[5], T1black3=displayable[6],
                            T2black1=displayable[7], T2outlier1=displayable[8], 
                            T2color1=displayable[9], T2black2=displayable[10], 
                            T2outlier2=displayable[11], T2color2=displayable[12], 
                            T2black3=displayable[13], T3black1=displayable[14], 
                            T3outlier1=displayable[15], T3color1=displayable[16],
                            T3black2=displayable[17], T3outlier2=displayable[18], 
                            T3color2=displayable[19], T3black3=displayable[20])
    
    
def getBreaks(tweet, sentiPerWord):
    
    breakIndex = []
    words = tweet.split(' ')
    for i in range(len(sentiPerWord)):
        if sentiPerWord[i]!='b':
            breakIndex.append(i)
            
    blackSet1 = ' '.join(words[0:breakIndex[0]])
    outlier1 = words[breakIndex[0]]
    if sentiPerWord[breakIndex[0]]=='r':
        color1 = 'red'
    else:
        color1='green'

    blackSet2 = ' '.join(words[breakIndex[0]+1:breakIndex[1]])
    outlier2 = words[breakIndex[1]]
    
    if sentiPerWord[breakIndex[1]]=='r':
        color2 = 'red'
        
    else:
        color2='green'
    blackSet3 = ' '.join(words[breakIndex[1]+1:])
        
    return blackSet1, outlier1, color1, blackSet2, outlier2, color2, blackSet3
  
  
@app.route('/helpme', methods = ['GET','POST'])
def helpme():
    return render_template('helpme.html')
    
    
@app.route('/prices', methods = ['GET','POST'])
def prices():
    return render_template('prices.html')
    
    
#main('aapl', 1)
if __name__ == "__main__":
    app.run()
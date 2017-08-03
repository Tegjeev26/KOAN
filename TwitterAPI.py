import string, os, datetime
import numpy as np
import matplotlib.pyplot as plt
import twitter
from GetOldTweets import got3

consumer_key='LZedcCMbUoRRMtkfNnF9jqXQC'
consumer_secret='EjY60p2nqxbHRqwdbSkr68HbGIMXeWhYR81BYkuaKlkM0VCoL4'
oauth_token='517112590-a0bWwypsSspHT9L6sT1jhK2ifKYLW7CufWCZryOD'
oauth_token_secret='BtQwOg7UyxS9RO8zmIHdInwScy9ehBspZs0D6lJYYjpCx'

api = twitter.Api(consumer_key='LZedcCMbUoRRMtkfNnF9jqXQC',
    consumer_secret='EjY60p2nqxbHRqwdbSkr68HbGIMXeWhYR81BYkuaKlkM0VCoL4',
    access_token_key='517112590-a0bWwypsSspHT9L6sT1jhK2ifKYLW7CufWCZryOD',
    access_token_secret='BtQwOg7UyxS9RO8zmIHdInwScy9ehBspZs0D6lJYYjpCx')

def getTweets(rawStock, dates):
    stock = '$' #seach symbol for stocks on twitter
    for letter in rawStock:
        if letter in string.ascii_letters:
            letter = letter.upper() #standardize stock to uppercase
            stock = stock + letter
            
    tweets = dict()
    for day in dates:
        tweetCriteria = got3.manager.TweetCriteria().setQuerySearch(stock).setSince(day).setUntil(dateIncrementer(day)).setMaxTweets(4)
        try:
            if got3.manager.TweetManager.getTweets(tweetCriteria) != []:
                tweets[day] = extractTweets(tweetCriteria) #add a set of tweets to the dictionary of days      
        except:
            pass
    return tweets

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
    if month==0: month=12
    if month<10:
        month = '0'+ str(month)
    else: month = str(month)
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
    
    
###repeated code - temporary
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
###end of repeated code
    

def evaluateSenti(tweets):
    score = 0
    for tweet in tweets:
        score += evaluate(tweet)
    return score/len(tweets)


###creates dictionary for bag of words approach
vals = dict()

file = open('polarity.txt' , encoding='utf-8')
infile = file.read()
infile=infile.splitlines()
for x in infile:
    x = x.strip()
    pieces = x.split(" ") #breaks down the polarity file into pieces
    vals[str(pieces[0])] = int(pieces[1])  #goes through all polarities and indexing them in value[]


def evaluate(tweet):
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
        net = 0-(neg/num_neg)
    else:
        net = (pos/num_pos) - (neg/num_neg)
    total = (net/5)
    return total
    
def getSentiments(stock, timePeriod):
    #gets overall trend in sentiment towards the company
    #start from previous month and go back as far as necessary
    dates = getDates(timePeriod)

    tweets_of_days = getTweets(stock, dates)

    sentiments = []
    for tweets in tweets_of_days:
        sentiments.append(evaluateSenti(tweets_of_days[tweets]))
    
    return sentiments, dates

print(getSentiments('aapl', 0.5))

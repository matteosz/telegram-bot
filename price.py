import pandas as pd
import  json, requests
import os
from datetime import datetime
from datetime import date
from datetime import timedelta

price = { 'Italy' : {},
          'Germany' : {}  ,
          'France' : {}  ,
          'Spain' : {}  ,
          'England' : {} }
currencies = {
    '€' : 'EUR',
    '£' : 'GBP',
    '$' : 'USD'
}
filename = ['price_history/',"conv_rates.json"]
url = 'https://v6.exchangerate-api.com/v6/' + str(os.getenv('PRICE_TOKEN')) + '/latest/EUR'

# Generate the directory price history if not present in the server
current_directory = os.getcwd()
final_directory = os.path.join(current_directory, r"price_history")
if not os.path.exists(final_directory):
   os.makedirs(final_directory)

class Currency_convertor:

    rates = {}
    def __init__(self, url):

        current_date = date.today()

        try: 
            with open(filename[1], 'r') as openfile:
                self.rates = json.load(openfile)
                previous_date = datetime.strptime(self.rates['Date'], '%Y/%m/%d')
        except:
            previous_date = date(year=2020,month=1, day = 1) # 01/01/2020

        if current_date >= previous_date + timedelta(days=5):# Older than 5 days
            data = requests.get(url).json()
    
            # Extracting only the rates from the json data
            self.rates = data["conversion_rates"]
            self.rates['Date'] = str(current_date)

            with open(filename[1], "w") as outfile:
                json.dump(self.rates, outfile)
 
    def convert(self, from_currency, amount): # to EUR
        amount = int(round(amount / self.rates[from_currency]))
        return amount

def read_price(search):
    try:
        df = pd.read_csv(filename[0] + search.replace(' ','_') +'.csv')
    except:
        print('No previous price history found for product ' + search)
        return pd.DataFrame(price).T.rename_axis('Country').reset_index()

    return df

def save_price(df, search):
    df.to_csv(filename[0] + search.replace(' ','_') +'.csv',index=False)


def convert_price(word): # Return price in EUR
    c = Currency_convertor(url)
    currency = currencies[word[:1]]
    money = int(word[1:])

    if currency == 'EUR':
        return money
  
    return c.convert(currency, money)
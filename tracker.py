from datetime import date
from driver import run_driver, close_driver, create_driver
from price import save_price, read_price, convert_price
from notify import alert
import time

europe = {'Italy' : 'it/',
        'Germany' : 'de/',
        'France' : 'fr/',
        'Spain'  : 'es/',
        'England' : 'co.uk/'}

def track_product(search, threshold,chat_id,clock):
    
    round = 0
    # Infinite loop
    while True:

        round += 1
        print(search + ' -> Round ' + str(round))

        current_date = str(date.today())
        driver = create_driver()

        # Read previous prices from the csv file
        price = read_price(search)

        # Iterate through the different european countries
        found_prices = []
        converted_prices = []
        links = []
        for suffix in europe.values():
            x,y = run_driver(driver,suffix,search,threshold)

            found_prices.append(x)
            if x == '-':
                converted_prices.append(-1)
            else:
                converted_prices.append(convert_price(found_prices[-1]))
            links.append(y)
        
        # Check if for the given product there's already a list of prices for the current date
        if current_date in price:
            column = list(price[current_date])
            for i in range(len(column)):
                if converted_prices[i] != -1 and (int(column[i]) == -1 or int(column[i]) > converted_prices[i]):
                    column[i] = converted_prices[i]
                    if converted_prices[i] <= 1.05 * threshold:
                        alert(converted_prices[i],links[i],chat_id)
        else:
            column = converted_prices
            last_col = price.iloc[:,-1:].values.tolist()
            for i in range(len(column)):
                if converted_prices[i] != -1 and converted_prices[i] <= 1.05 * threshold:
                    if last_col[i][0] in europe.keys() or int(last_col[i][0]) != converted_prices[i]: # trigger if different price occurred
                        alert(converted_prices[i],links[i],chat_id)

        price[current_date] = column

        # Save prices in the csv file
        save_price(price,search)

        #Close the driver
        close_driver(driver)

        time.sleep(clock)
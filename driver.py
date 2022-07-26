from cmath import inf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from string_process import compare, extract_subitem
import re, os

europe = {'it/' : 'Italy' ,
          'de/' : 'Germany' ,
          'fr/' : 'France' ,
          'es/' : 'Spain' ,
          'co.uk/' : 'England'}
url = 'https://www.amazon.'
err_val = '-'
err_link = ''

def create_driver():
    # Create service and options for the Chrome driver - Heroku Config
    service = ChromeService(executable_path=ChromeDriverManager().install())
    options = ChromeOptions()

    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    #options.add_argument('--headless')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument('--log-level=1')
    return webdriver.Chrome(service=service,options=options)
    #return webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),options=options)

def run_driver(driver,suffix,search,threshold):

    search = search.split(' ')
    try:
        search = search.remove('')
    except:
        pass

    # Go to Amazon
    try:
        driver.get(url + suffix)
    except:
        print('Impossible to reach Amazon ' + europe[suffix])
        return err_val, err_link

    # wait the loading of the page
    driver.implicitly_wait(10) 

    # Search the product
    try:
        search_box = driver.find_element(by=By.ID, value="twotabsearchtextbox")
        search_button = driver.find_element(by=By.ID, value="nav-search-submit-button")
        search_box.send_keys(' '.join(search))
        search_button.click()
    except:
        print('Buttons not found in the region ' + europe[suffix])
        return err_val, err_link

    # wait the loading of the page
    driver.implicitly_wait(10)

    # Find the closest match
    #items = driver.find_elements(by=By.CSS_SELECTOR, value="a[class='a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'") # find all the links of the products in the page
    items = driver.find_elements(by=By.CSS_SELECTOR, value="div[class='s-card-container s-overflow-hidden aok-relative s-expand-height s-include-content-margin s-latency-cf-section s-card-border']") # find all products in the main page
    if len(items) == 0:
        items = driver.find_elements(by=By.CLASS_NAME, value='sg-col-inner')

    max_value = -1
    min_price = inf
    product_url = ''

    for item in items:
        text = item.get_attribute('innerHTML')
        #description = re.sub("<.*?>", '',items[i].get_attribute('innerHTML')) # extract the product description
        description = extract_subitem('<span class="a-size-base-plus a-color-base a-text-normal">(.*?)<', text)
        amount = extract_subitem('<span class="a-price-whole">(.*?)<', text)

        if description is None:
            description = extract_subitem('<span class="a-size-medium a-color-base a-text-normal">(.*?)<', text)
            if description is None:
                continue
        if amount is None:
            amount = inf
        else:
            amount = int(amount.replace('"','').replace(',','').replace('.','').replace(' ','').replace('\u202f','')[:-2])
        
        c = compare(description,search)
        
        if c > max_value or (c == max_value and amount < min_price) and amount >= 0.5 * threshold: # take the most accurate description, if even then take lowest price
            max_value = c
            min_price = amount
            #product_url = item.get_attribute('href')
            product_url = url + suffix[:-1] + extract_subitem('<a class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal" href="(.*?)">', text)
    
    if max_value == -1:
        print('Impossible to find the product with your keywords in Amazon ' + europe[suffix])
        return err_val, err_link

    # Open the product page
    try:
        driver.get(product_url)
    except: 
        print('Impossible to reach Amazon ' + europe[suffix] + "'s product page")
        return err_val, err_link
    
    # wait the loading of the page
    driver.implicitly_wait(10) 

    # Check if the seller is Amazon and item is new
    price_value = str(min_price)
    try:
        currency = driver.find_element(by=By.CLASS_NAME, value="a-price-symbol").get_attribute('innerHTML') # extract currency information
    except:
        print('Product not available from Amazon ' + europe[suffix])
        return err_val, err_link

    try:
        option1 = driver.find_elements(by=By.CLASS_NAME, value="a-size-small") # seller and sender
        option2 = re.sub("<.*?>", '',driver.find_element(by=By.ID, value='merchant-info').get_attribute('innerHTML')).replace(' ','').replace('\n','')
    except: 
        option2 = ''

    i = 0
    for item in option1:
        if item.get_attribute('innerHTML') == 'Amazon':
            i += 1
        if i == 2:
            break

    if i == 2 or option2 == 'DispatchedfromandsoldbyAmazon.':
        print('Product found from Amazon ' + europe[suffix] + ' at ' + currency + price_value)
        return currency + price_value, product_url
    
    print('Product not sold from Amazon in ' + europe[suffix])
    return err_val, err_link

def close_driver(driver):
    driver.quit()
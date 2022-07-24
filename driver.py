from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from string_process import compare
import re

europe = {'it/' : 'Italy' ,
          'de/' : 'Germany' ,
          'fr/' : 'France' ,
          'es/' : 'Spain' ,
          'co.uk/' : 'England'}
url = 'https://www.amazon.'
err_val = '-'
err_link = ''

def create_driver():
    # Create service and options for the Chrome driver
    service = ChromeService(executable_path=ChromeDriverManager().install())
    options = ChromeOptions()
    # Not displaying the driver
    options.add_argument('--headless')

    return webdriver.Chrome(service=service,options=options)

def run_driver(driver,suffix,search):

    search = search.split(' ')
    try:
        search = search.remove('')
    except:
        pass
    keywords_count = len(search)

    # Go to Amazon
    try:
        driver.get(url + suffix)
    except:
        print('Impossible to reach Amazon ' + europe[suffix])
        return err_val,err_link

    # wait the loading of the page
    driver.implicitly_wait(5) 

    # Search the product
    try:
        search_box = driver.find_element(by=By.ID, value="twotabsearchtextbox")
        search_button = driver.find_element(by=By.ID, value="nav-search-submit-button")
        search_box.send_keys(' '.join(search))
        search_button.click()
    except:
        print('Buttons not found in the region ' + europe[suffix])
        return err_val,err_link

    # wait the loading of the page
    driver.implicitly_wait(5)

    # Find the closest match
    items = driver.find_elements(by=By.CSS_SELECTOR, value="a[class='a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'") # find all the links of the products in the page
    max_value = -1
    product_url = ''
    for item in items:
        description = re.sub("<.*?>", '',item.get_attribute('innerHTML')) # extract the product description
        c = compare(description,search)
        if c > max_value: # take the most accurate description but at least 85% compliant
            max_value = c
            product_url = item.get_attribute('href')
            if c == keywords_count: # perfect match = all searched keywords in the product description
                break
    
    if max_value == -1:
        print('Impossible to find the product with your keywords in Amazon ' + europe[suffix])
        return err_val,err_link

    # wait the loading of the page
    driver.implicitly_wait(5)

    # Open the product page
    try:
        driver.get(product_url)
    except: 
        print('Impossible to reach Amazon ' + europe[suffix] + "'s product page")
        return err_val,err_link
    
    # wait the loading of the page
    driver.implicitly_wait(5) 

    try:
        currency = driver.find_element(by=By.CLASS_NAME, value="a-price-symbol").get_attribute('innerHTML')
        price_value = re.sub("<.*?>", '',driver.find_element(by=By.CLASS_NAME, value="a-price-whole").get_attribute('innerHTML').replace('"','').replace(',','').replace('.','').replace(' ','').replace('\u202f','')) # extract price value
    except:
        print('Product not available from Amazon ' + europe[suffix])
        return err_val,err_link

    option2 = ''

    try:
        option1 = driver.find_elements(by=By.CLASS_NAME, value="a-size-small") # seller and sender
        option2 = re.sub("<.*?>", '',driver.find_element(by=By.ID, value='merchant-info').get_attribute('innerHTML')).replace(' ','').replace('\n','')
    except: 
        pass

    i = 0
    for item in option1:
        if item.get_attribute('innerHTML') == 'Amazon':
            i += 1
        if i == 2:
            break

    if i == 2 or option2 == 'DispatchedfromandsoldbyAmazon.':
        print('Product found from Amazon ' + europe[suffix] + ' at ' + currency + price_value)
        return currency + price_value,product_url
    
    print('Product not sold from Amazon in ' + europe[suffix])
    return err_val,err_link

def close_driver(driver):
    driver.quit()
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import time
import random


def create_url(name_parts, weapon_parts): #creating a function to build the url from the information in the dataframe
    weapon = '+'.join(weapon_parts) #joining name_parts and weapon_parts with a + symbol which is needed for the url
    skin = '+'.join(name_parts)
    # Constructing the URL
    url = f"https://steamcommunity.com/market/search?category_730_ItemSet%5B%5D=any&category_730_ProPlayer%5B%5D=any&category_730_StickerCapsule%5B%5D=any&category_730_TournamentTeam%5B%5D=any&category_730_Weapon%5B%5D=any&category_730_Quality%5B%5D=tag_normal&appid=730&q={weapon}+%7C+{skin}"
    print(url)
    return url

def read_line_and_create_url(df, i):
    weapon_type = df.loc[i,"Weapon type"] 
    skin_name = df.loc[i,"Skin"]
    # spliting the weapon_type and skin_name into separate words to construct the url        
    weapon_words = weapon_type.split() 
    skin_words = skin_name.split() 
    url = create_url(skin_words, weapon_words)
    return url

def rotate_proxy(url,proxies, counter):
# Scraping the prices and conditions from the Steam market
    try:
        request = requests.get(url, proxies = {"http":"http://" + proxies[counter]})  # using the list of proxies for the requests 
        soup = BeautifulSoup(request.text, features="html.parser")  # try requesting, if success, rotate to the next proxy
        counter += 1
        return soup
    except IndexError:
        counter = 0
        request = requests.get(url, proxies = {"http":"http://" + proxies[counter]})
        soup = BeautifulSoup(request.text, features="html.parser")  # if experiencing IndexError (meaning the rotation reached the last proxy) reset the counter 
                                                                    # back to the original proxy and then request, then go to another proxy
        counter += 1
        return soup
    except requests.exceptions.ConnectionError:  # this error occurs when the requests are denied by the sever (not just a 429)
        time.sleep(60)  # wait 60 seconds then retry
        counter = 0
        request = requests.get(url, proxies = {"http":"http://" + proxies[counter]})
        soup = BeautifulSoup(request.text, features="html.parser")
        counter += 1
        return soup
    
    
def read_soup_and_build_df(soup,df,i):
    items = soup.find_all("div", class_="market_listing_row")
    for item in items:
        item_name = item.find("span", class_="market_listing_item_name").get_text(strip=True) 
        condition = item_name.split("(")[-1].strip(")")  # extracting conditions 
        prices = item.find_all("span", class_="sale_price") #extracting prices for all conditions at once which saves us requests
        prices_text = np.array(prices) #creating a numpy array from the prices
        prices_clean = np.char.strip(prices_text, "\r\n\t\t\t\t\t\t") #Cleaning the exctracted values
            
        if str(condition) == "Factory New":
            df.loc[i, "Factory New"] = prices_clean
        elif str(condition) == "Minimal Wear":
            df.loc[i ,"Minimal Wear"] = prices_clean
        elif str(condition) == "Field-Tested":
            df.loc[i ,"Field-Tested"] = prices_clean
        elif str(condition) == "Well-Worn":
            df.loc[i ,"Well-Worn"] = prices_clean
        elif str(condition) == "Battle-Scarred":
            df.loc[i ,"Battle-Scarred"] = prices_clean                
        #note that these are sale prices, eg an ammount that seller receives after the sale
    return df

def read_all(df):
    with open("utilities/proxy_list_final.txt", "r") as f: # reading a list of proxies obtained fron a website
        proxies = f.read().split("\n")
    counter = 0  # creating a counter for purpouse of rotating proxies
    for i in range(0,len(df)):
        
        url = read_line_and_create_url(df, i)
        
        soup = rotate_proxy(url, proxies, counter)
        
        read_soup_and_build_df(soup,df,i)
        
        df.to_csv("utilities/allvalues.csv", index=False)
        time.sleep(random.uniform(9,10)) #wait 9 to 10 seconds due to request rate limiter on steam market 
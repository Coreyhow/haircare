#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 14:35:55 2025

@author: corey
"""

import requests
from bs4 import BeautifulSoup
import sql
#created a function to webscrape the ingredients

def ingredients(row):
    product = requests.get(row)
    scrape = BeautifulSoup(product.text,'html.parser')
    list_of_ingredients = scrape.find_all("div", {'class': "Markdown Markdown--body-2 Markdown--left"})
    
    #in case of an out of index error 
    if len(list_of_ingredients) >=3:
        header = list_of_ingredients[2]
        text = header.find_all("p")
        ingredients_list = [x.strip().rstrip(".") for x in text[0].get_text().split(",")]
        print(ingredients_list)
        return sql.sqlinsert(ingredients_list)
productcount=0
pagecount=1          
#pulling data from ulta from the pages
for page in range(1,3):
    print(f"page {page}")
    conditioner = f'https://www.ulta.com/shop/hair/shampoo-conditioner/leave-in-conditioner?page={pagecount}'
    print(conditioner)
    pagecount+=1 
    count= 0
    response= requests.get(conditioner)
    soup = BeautifulSoup(response.text,'html.parser')
    #print(soup.prettify())
    
    
    #webscrape the links for the product
    list_of_elements = soup.find_all("li", {'class':"ProductListingResults__productCard"})
    
    #creates a list for all of the list of products on page 1
    for row in list_of_elements:
        productcount+=1
        #gives the url of the product
        urls= row.a['href']
        print(urls)
        ingredients(urls)
        print(f"Product {productcount}")
        print(f"page {page}")  
    
        
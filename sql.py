#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 10:24:13 2025

@author: corey
"""
import sys
print(sys.executable)
import mysql.connector
import requests


#Connection to the database
mydb = mysql.connector.connect(
    host="localhost",
    user="corey",
    password="Haircare820x",
    database="haircare"
)

mycursor = mydb.cursor()

#Turn the ingredients string into a list for sql insertion
def sqlinsert(y):
    sql2 = """SELECT ingredientID FROM ingredients WHERE ingredientName = %s"""
    insert_sql = """INSERT INTO haircare.Ingredients (ingredientID, ingredientName) VALUES (%s, %s)"""
    mycursor.execute("SELECT MAX(ingredientID) FROM ingredients;")
    result = mycursor.fetchone()
    next_id = int(result[0]) + 1 if result and result[0] is not None else 1
    for ingredient in y:
        try:
            # Check if the ingredient already exists
            mycursor.execute(sql2, (ingredient,))
            existing = mycursor.fetchone()
            if (len(ingredient)>255):
                continue
            if existing:
                print(f"<p>Ingredient '{ingredient}' already exists with ID {existing[0]}.</p>")
            else:
                # Assign a new ID and insert
                mycursor.execute(insert_sql, (next_id, ingredient))
                print(f"<p>Inserted new ingredient '{ingredient}' with ID {next_id}.</p>")
                next_id += 1  # Increment only for successful inserts
        except requests.exceptions.ContentDecodingError:
            print("Warning: Content decoding failed for. Skipping...")


    mydb.commit()

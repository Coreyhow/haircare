#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 10:24:13 2025

@author: corey

Legacy helper for the old scraper scripts; now writes to SQLite via db.py.
New code should use scraper.py.
"""
import db

mydb = db.connect()


def sqlinsert(y):
    """Insert ingredient names that don't exist yet."""
    with mydb:
        for ingredient in y:
            if ingredient and len(ingredient) <= 255:
                db.get_or_create_ingredient(mydb, ingredient)

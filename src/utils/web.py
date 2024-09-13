"""
utils/web.py

This module provides utility functions related to web operations. 
Currently, it includes a function for opening URLs in the default web browser.

Functions:
    open_link - Opens the provided URL in the system's default web browser.
"""

import webbrowser

def open_link(url):
    """
    Opens the provided URL in the default web browser.
    
    Args:
        url (str): The web address to be opened.
    
    Raises:
        ValueError: If the URL is empty or None.
    """
    if not url:
        raise ValueError("The URL provided is invalid or empty.")
    
    webbrowser.open(url)

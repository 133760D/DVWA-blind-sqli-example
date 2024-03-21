#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 25 00:35:14 2024

@author: Alexandre Maurin
"""
import requests
import bs4 as bs
import time

class dvwa():
    PAGE_LOADING_TIMEOUT:float = 15.0
    RETRY_TIMEOUT:float = 1.0
    
    def __init__(self, host="http://localhost") -> None:
        self.host = host
        self.LOGIN_PATH = f"{host}/login.php"
        self.SETUP_PATH = f"{host}/setup.php"
        self.BLIND_SQLI_PATH = f"{host}/vulnerabilities/sqli_blind/"
        return
    
    def makeSession(self) -> requests.Session:
        self.host
        self.session = requests.Session()
        ##r = self.session.get(self.host)
        ##bs_parsed = bs.BeautifulSoup(r.text, 'lxml')
        #user_token = bs_parsed.select_one("#content > form:nth-child(1) > input:nth-child(2)").get('value')
        #wait for the page to load if the environment is not loaded
        max_retry = 0
        while (bs_parsed := bs.BeautifulSoup(self.session.get(self.host).text, 'lxml').select_one("#content > form:nth-child(1) > input:nth-child(2)")) is None:
            if max_retry > self.PAGE_LOADING_TIMEOUT:
                raise TimeoutError("Element missing - login form not loading. Is the host reachable?")
            time.sleep(self.RETRY_TIMEOUT)
            max_retry+= self.RETRY_TIMEOUT
        user_token = bs_parsed.get('value')
        self.session.post(self.LOGIN_PATH, data={'username': 'admin', 'password': 'password', 'Login': 'Login', 'user_token': user_token})
        return self.session
    
    def createDatabase(self) -> None:
        self.__sessioncheck("createDatabase")
        #get the user token, old user_token might be expired
        r = self.session.get(self.SETUP_PATH)
        bs_parsed = bs.BeautifulSoup(r.text, 'lxml')
        user_token = bs_parsed.select_one("div.body_padded:nth-child(1) > form:nth-child(64) > input:nth-child(2)").get('value')
        self.session.post(self.SETUP_PATH, data={'create_db': 'Create / Reset Database', 'user_token': user_token})
        return
    
    def resetDatabase(self) -> None:
        self.__sessioncheck("resetDatabase")
        self.createDatabase()
        return
    
    def __sessioncheck(self, funcname:str) -> None:
        if not hasattr(self, 'session'):
            raise AttributeError(f'Called #{funcname} before initializing session.')
        return
import time
import re

from django.conf import settings

from bs4 import BeautifulSoup

import selenium.webdriver.support.ui as ui
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

import logging
logger = logging.getLogger("applog")

"""
Functions for retrieving information from adsl2exchanges.com.au
"""
class ADSL2:

    """
    @max_attempts:
        Amount of attempts that can be made when trying to retrieve
        data from the adsl2exchanges.com.au page
    """
    def __init__(self, max_attempts=2):
        self.max_attempts = max_attempts

    """
    Get line distance and possible speed for an address from 
    adsl2exchanges.com.au

    @address:
        The address to check against in the form of
        a string

    @browser:
        A selenium browser object

    @retry_wait:
        The amount of time in seconds before retrying an address
    """
    def get(self, address, browser, retry_wait=2):
        attempts = 0
        wait = ui.WebDriverWait(browser, 3)

        while (True):
            browser.get(settings.ADSL_URL)

            try:
                form = browser.find_elements_by_tag_name("form")[2]
            except IndexError:
                raise NoSuchElementException

            form_address = form.find_element_by_name("Address")
            form_address.send_keys(address + Keys.RETURN)

            try:
                try:
                    wait.until(lambda browser: browser.find_element_by_id("map").get_attribute("innerHTML").strip() != "")
                except TimeoutException:
                    pass

                adsl_source = BeautifulSoup(browser.find_element_by_id("map").get_attribute("innerHTML"))
                divs = [x for x in adsl_source.findAll("div") if "Estimated" in x.getText()]

                if len(divs) > 0:
                    adsldata = divs[len(divs) - 1]
                else:
                    raise NoSuchElementException

                values = re.findall('(\d+[.]?[\d]+)', str(adsldata))

                try:
                    return {
                        'crow_fly_distance': values[0],
                        'cable_length': values[1],
                        'estimated_speed': values[2]
                    }
                except IndexError:
                    raise NoSuchElementException

            except NoSuchElementException:
                # Some sort of error occurred! Either the address is malformed,
                # or the server is having some sort of issue. We'll wait a little bit
                # and try again
                if attempts < self.max_attempts:
                    attempts += 1
                    # Wait 1 seconds before trying again
                    time.sleep(retry_wait)
                    logger.debug("... ... ... Failed to parse the address. Trying again. Attempt #" + attempts)
                    continue
                else:
                    logger.debug("... ... ... Failed all attempts. Skipping.")
                    return None            
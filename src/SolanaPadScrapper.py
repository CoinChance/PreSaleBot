
import re
import time
import math
import logging
from typing import Optional, Dict, Tuple, List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from src.TokenData import TokenData
from src.BaseScrapper import BaseScrapper
from src.Chains import Chains

class SolanaPadScrapper(BaseScrapper):
    def __init__(self, logging: logging.Logger) -> None:
        """
        Initialize the SolanaPadScrapper class.

        This function is the constructor of the class. It is called when an
        instance of the class is created. It initializes the superclass
        BaseScrapper with the logging object, and sets the base URL for
        SolanaPad launchpads.

        Arguments:
            logging: The Python logger to use for logging messages.
        """
        super().__init__(logging)
        self.logging.debug("Initializing the SolanaPadScrapper class.")
        self._url = "https://solanapad.io/launchpad-list"
        self.logging.debug("Set the base URL to %s", self._url)
             
    def start_driver(self) -> bool:
        """Start the Selenium driver and return its status."""
        super().start_driver()

        status: bool = False
        try:
            if super().get_status():
                self.driver.get(self._url)

                live_menu: WebElement = self.driver.find_element(By.XPATH, "//li[contains(@data-menu-id, 'live')]")
                live_menu.click()

                WebDriverWait(self.driver, self.timeout).until(EC.visibility_of_element_located((By.TAG_NAME, "body")))

                for _ in range(self.scroll_downs):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(self.timeout)

                self._extract_links()
                status = True
                self.logging.info("Successfully opened URL %s", self._url)
        except Exception as ex:
            self.logging.error("Exception (%s) occured while Opening URL %s", ex, self._url)

        return status

    def _extract_links(self) -> int:
        """
        Extract links from SolanaPad website.

        This function iterates over all divs that have a class 'py-5 px-3 lg:p-6
        bg-[#18182B] rounded-2xl flex flex-col gap-4 text-base' and finds
        the one that contains the string 'View more'. This indicates that the
        div is showing information about a live project. After finding the
        live project div, it extracts all links from that div and finds the
        one that starts with '/launchpad-list/'. That link is then appended
        to self._links and the total number of links extracted is returned.

        Returns:
            The total number of links extracted.
        """
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        # Find all divs with the class name 'py-5 px-3 lg:p-6 bg-[#18182B]
        # rounded-2xl flex flex-col gap-4 text-base'
        divs = soup.find_all("div", class_="py-5 px-3 lg:p-6 bg-[#18182B] rounded-2xl flex flex-col gap-4 text-base")
        links_count: int = 0
        live_count: int = 0

        for div in divs:
            # Find the element in the div that contains the string 'View more'
            element = div.find(string='View more')
            # If no such element was found, skip to the next div
            if element is None:
                continue
            # Increment the live_count variable to keep track of the number of
            # live projects found
            live_count += 1

            print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
            # Find all links in the div
            links = div.find_all('a')

            for link in links:
                # Extract the href attribute
                href = link.get('href')
                print('href: ', href)
                # If the href starts with '/launchpad-list/', it is the link we
                # are looking for, so append it to self._links
                if href.startswith('/launchpad-list/'):
                    link = f'https://solanapad.io{href}'
                    self._links.append(link)
                    links_count += 1
                    self.logging.info('URL: %s', link)
                    break

        self.logging.info('Total Live Projects: %d, Scrapped Links: %d', live_count, links_count)
        return links_count

    def _extract_social_media_info(
        self,
        soup: BeautifulSoup,        
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extract social media links from the soup.

        Args:
            soup: The BeautifulSoup object containing the page.            

        Returns:
            A tuple containing Twitter, Telegram, and Website links.
        """
        twitter_link: Optional[str] = None
        telegram_link: Optional[str] = None
        website_link: Optional[str] = None
        name: Optional[str] = None

        #divs = soup.find_all("div", class_="flex items-center gap-2.5 text-gray-500 mt-2 justify-center")
        divs = soup.find_all("div", class_="flex flex-col lg:flex-row justify-between gap-2 lg:gap-5")   

        for div in divs:
            if name is None:
                try:
                    # Find the <span> element with the specified classes
                    span_element = div.find('span', class_='font-bold uppercase')

                    # Extract the text from the <span> element
                    name = span_element.text.strip()
                except Exception as e:
                    pass

            links = div.find_all("a")
            for link in links:
                href = link.get("href")
                if "twitter.com" in href or "x.com" in href:
                    if "intent/tweet?" in href:
                        continue
                    twitter_link = href
                elif "t.me" in href or "telegram.me" in href:
                    if "share/msg" in href:
                        continue
                    telegram_link = href
                elif (
                    "discord" in href
                    or "facebook.com" in href
                    or "github.com" in href
                    or "reddit.com" in href
                    or "medium.com" in href
                    or "youtube.com" in href
                    or "instagram.com" in href
                    or "whatsapp.com" in href
                    or "linkedin.com" in href
                ):
                    continue
                elif href.startswith('/'):
                    continue
                else:
                    website_link = href

        return name, twitter_link, telegram_link, website_link

    def _extract_raised(self) -> Optional[str]:
        """
        Extract the raised amount from the canvas element.

        This function tries to find a <div> element with the class "mt-4 bg-[#21283A] p-4 rounded-2xl"
        and searches for a percentage inside its text. If a percentage is found, it searches for
        a match using the regular expression '(\d+\.\d+%)', which captures the percentage into a group.
        If a match is found, it returns the first (and only) group of the match, which is the captured
        percentage. Otherwise, it returns None.

        Arguments:
            None

        Returns:
            The percentage raised (e.g., "16.811%"), or None if the percentage could not be found.
        """
        # Define regular expression to capture the percentage value
        percentage_regex = r'(\d+\.\d+%)'  # Matches the percentage (e.g., 16.811%)

        # Initialize variable to store the percentage
        Raised = None

        try:
            # Parse the HTML page source using BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # Find all <div> elements with the specified classes
            divs = soup.find_all('div', class_="mt-4 bg-[#21283A] p-4 rounded-2xl")

            # Iterate through each <div> element
            for div in divs:

                # Check if the text of the <div> element contains a percentage
                if '%' in div.text:

                    # Search for a match using the regular expression
                    percentage_match = re.search(percentage_regex, div.text)

                    # If a match is found, extract the percentage from the match
                    Raised = percentage_match.group(1) if percentage_match else None

                    # Return the percentage if it was found, or None if not found
                    return Raised

        except Exception as e:
            # Log the error if there is an exception
            self.logging.error(f"Error: {e}")

        # Return None if the code reaches this point
        return None

    def extract_data(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            proj_chain: Optional[str] = None  # The chain name for the project
            token_info: Dict[str, str] = {}  # The dictionary to store all the token data
            
            # supply = self._extract_total_supply()
            Raised = self._extract_raised()
            if Raised is not None:
                token_info['Raised'] = Raised
          

            # Find all divs with class "transition-all"
            divs = soup.find_all(class_="text-xs lg:text-base flex flex-col gap-4 mt-6")
            
            for div in divs:  # Loop through each div
                ele = div.find_all('li', class_="flex justify-between items-center gap-5")
                for li in ele:
                    if li is None:
                        continue
                    try:
                       # Find the <span> elements within the <li> element
                        span_elements = li.find_all('span')

                        # Extract the label and value
                        label = span_elements[0].text.strip()
                        if label is None:
                            continue  # Skip this div if the label is not found

                        value = span_elements[1].text.strip()
                        if value is None:
                            continue  # Skip this div if the value is not found

                        if label == "Address":
                            # Split the value at "Do not" and take the first segment
                            value = value.split('Do not ')[0].strip()

                        
                        # If this is the first label-value pair with the "Address" label,
                        # extract the chain name from the value
                        if proj_chain is None:
                            proj_chain, symbol = self._extract_chain(label, value)
                            if proj_chain is not None:
                                token_info['Chain'] = proj_chain
                                token_info['Symbol'] = symbol

                        # Store the label and value in the token_info dictionary
                        token_info[label] = value
                    except Exception as ex:
                        self.logging.error("Error extracting data: %s", ex)


            token_info['Status'] = 'Sale live'

            name, twitter, telegram, website = self._extract_social_media_info(soup)
            if twitter is None:
                self.logging.error("Twitter link not found")
                token_info['Twitter'] = "Not Available"  # If the Twitter link is not found, set the Twitter key to "Not Available"
            else:
                token_info['Twitter'] = twitter  # Otherwise, set the Twitter key to the Twitter link

            if telegram is None:
                self.logging.error("Telegram link not found")
                token_info['Telegram'] = "Not Available"  # If the Telegram link is not found, set the Telegram key to "Not Available"
            else:
                token_info['Telegram'] = telegram  # Otherwise, set the Telegram key to the Telegram link

            if website is None:
                self.logging.error("Website link not found")
                token_info['Website'] = "Not Available"  # If the website link is not found, set the website key to "Not Available"
            else:
                token_info['Website'] = website  # Otherwise, set the website key to the website link 
        
            if name is None:
                self.logging.error("Name not found")
                name = "Not Available"
            else:
                token_info['Name'] = name

            return TokenData.solanapad_adapter(token_info)  # If there is no error, return the token data
        except Exception as ex:
            self.logging.error("Error extracting data: %s", ex)
            return None
    
    def _extract_chain(self, label: str, value: str) -> Optional[str]:
        """
        Extract chain from label and value.

        Args:
            label: The label to check for 'Rate' or 'rate'.
            value: The value to extract the chain from.

        Returns:
            The chain found in the value or None.
        """
        result: Optional[str] = None
        symbol: Optional[str] = None

        # Check if the label contains 'Rate' or 'rate'
        if 'Rate' in label or 'rate' in label:
            # Split the value by spaces
            words = value.split()

            # Filter words that are in the chains_array
            chains = [word for word in words if word in Chains]

            # Check if exactly one chain is found in the value
            if len(chains) == 1:
                result = chains[0]

                # Split the string by whitespace, and Extract the last element
                symbol = value.split()[-1]

                self.logging.debug("Found chain: %s", result)
            else:
                self.logging.debug("No valid chain found in the value.")
        else:
            self.logging.debug("Label does not contain 'Rate' or 'rate'.")

        return result, symbol
    
   
if __name__ == "__main__":
    scraper = SolanaPadScrapper(logging)
    status = scraper.start_driver()
    if status:
        links = scraper.get_links()
        total = len(links)
        print('Total Links: ', total)
    
    idx = 0
    #links = scraper.get_links()
    for link in links:
        status = scraper.open_sub_url(url=link)
        token = scraper.extract_data()
        #status = scraper.extract_token_info_strategy1(url="https://solanapad.io/launchpad-list/3wLDvfT9Gm4fp2mqHhcWouf1QFMLUCGSR8MrDvBbYSnK")
        
        
        if token is None:
            continue
        
        print(idx, ' ....................................')
        print("Name: ", token.name)
        print("Symbol: ", token.symbol)
        print("Token Address: ", token.token_address)
        print("Supply: ", token.supply)
        print("Soft Cap: ", token.soft_cap)
        print("Start Time: ", token.start_time)
        print("End Time: ", token.end_time)
        print("Lockup Time: ", token.lockup_time)
        print("Rate: ", token.rate)
        print("Raised: ", token.raised)
        print("Chain: ", token.chain)
        print("Web: ", token.web)
        print("Twitter: ", token.twitter)
        print("Telegram: ", token.telegram)
        print('......................................')
        idx = idx + 1
            
   

        
    # links = scraper.get_links()
    # for link in links:
    #     print(link.get_attribute('href'))
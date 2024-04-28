import time
import logging
from typing import Optional, Dict, Tuple, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from src.TokenData import TokenData
from src.BaseScrapper import BaseScrapper
from src.Chains import Chains


class PinkSaleScrapper(BaseScrapper):
    def __init__(self, logging: logging.Logger) -> None:
        super().__init__(logging)
        self._url = "https://www.pinksale.finance/launchpads" # Base URL for pinksale launchpads
        self._links: List[str] = [] # List of links scrapped from pinksale launchpads
        self.scroll_downs = 10  # Maximum Number of times to scroll down

    def start_driver(self) -> bool:
        super().start_driver()

        try:
            self.driver.get(self._url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(10)
            # Scroll down to load more data
            scroll_pause_time = 5  # Adjust as needed
            
            for _ in range(self.scroll_downs):
                # Scroll down by simulating the "END" key press
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                time.sleep(scroll_pause_time)
            time.sleep(5)
            self.status = True
            self._extract_links()
        except Exception as ex:
            self.status = False
            self.logging.error("Exception (%s) occured while Opening URL %s", ex, self._url)
        return self.status      
    
    def open_sub_url(self, url: str) -> bool:
        """
        Open a sub URL in the driver.

        Args:
            url: The URL to open.

        Returns:
            True if the URL was opened successfully, False otherwise.
        """
        # Set the maximum time to wait for elements to be loaded (in seconds)
        self.driver.set_page_load_timeout(10)

        # Set implicit wait time for elements to be located
        self.driver.implicitly_wait(10)

        try:
            # Attempt to open the URL
            self.driver.get(url)
            time.sleep(10)
            return True
        except Exception as e:
            # Log any exceptions during URL opening
            self.logging.error(f"Failed to open URL: {url}. Exception: {e}")

        return False

    def get_Status(self):
        return self.status
    
    def get_links(self):
        return self._links
    
    def extract_data(self) -> Optional[TokenData]:
        """
        Extract token data from the page source.

        The data is extracted from HTML elements with the class "transition-all".
        For each element, the label and value are extracted and stored in a dictionary.
        The chain is extracted from the label-value pair where label contains "Rate".
        If the chain is not found, the method logs an error and returns None.
        Twitter, Telegram, and website links are extracted from the page using the
        extract_social_media_info() method. If any of these links are not found,
        the corresponding key-value pair in the token_info dictionary is set to
        "Not Available".

        Returns:
            A TokenData object containing all the extracted data, or None if there is an error.
        """
        try:
            the_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            proj_chain: Optional[str] = None  # The chain name for the project
            token_info: Dict[str, str] = {}  # The dictionary to store all the token data

            # Find all divs with class "transition-all"
            divs = the_soup.find_all(class_="transition-all")
            for div in divs:  # Loop through each div
                try:
                    # Extract the label and value from each div
                    label = div.find(class_="flex-1 capitalize")
                    if label is None:
                        continue  # Skip this div if the label is not found
                    label = label.text.strip()  # Remove any whitespace from the label
                    value = div.find(class_="break-all")
                    if value is None:
                        continue  # Skip this div if the value is not found
                    value = value.text.strip()  # Remove any whitespace from the value

                    if label == "Address":
                        # Split the value at "Do not" and take the first segment
                        value = value.split('Do not ')[0].strip()
                    # If this is the first label-value pair with the "Address" label,
                    # extract the chain name from the value
                    if proj_chain is None:
                        proj_chain = self._extract_chain(label, value)

                    # Store the label and value in the token_info dictionary
                    token_info[label] = value
                except Exception as ex:
                    self.logging.error("Error extracting data: %s", ex)

            if proj_chain is None:
                self.logging.error("Chain not found")
                return None  # If the chain is not found, return None
            else:
                token_info['Chain'] = proj_chain  # Otherwise, set the chain name in the token_info dictionary

            twitter, telegram, website = self._extract_social_media_info(the_soup, token_info['Name'])
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

            # Adapt the dictionary to TokenData class
            return TokenData.pinksale_adapter(token_info)  # If there is no error, return the token data
        except Exception as e:
            self.logging.error("Error: %s", e)
            return None  # If there is an error, return None

    def _extract_links(self) -> int:
        """
        Extract links from PinkSale website.

        Returns:
            The total number of links extracted.
        """
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        divs = soup.find_all(class_="p-2")
        links_count = 0
        live_count = 0
        for div in divs:
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
            # Find all links in the div
            element = div.find(string='Sale live')
            if element is not None:
                live_count += 1
                links = div.find_all('a')
                print('----------------------------------------------')
                for link in links:
                    # Extract the href attribute
                    href = link.get('href')
                    print('href: ', href)
                    if href.startswith('/launchpad/') or href.startswith('/solana/launchpad/'):
                        link = 'https://www.pinksale.finance' + href
                        self._links.append(link)
                        links_count += 1
                        self.logging.info('URL: %s', link)
            else:
                self.logging.debug('Sale Not Live')
        self.logging.info('Total Live Projects: %d, Scrapped Links: %d' , live_count, links_count)
        return links_count

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

        # Check if the label contains 'Rate' or 'rate'
        if 'Rate' in label or 'rate' in label:
            # Split the value by spaces
            words = value.split()

            # Filter words that are in the chains_array
            chains = [word for word in words if word in Chains]

            # Check if exactly one chain is found in the value
            if len(chains) == 1:
                result = chains[0]
                self.logging.debug("Found chain: %s", result)
            else:
                self.logging.debug("No valid chain found in the value.")
        else:
            self.logging.debug("Label does not contain 'Rate' or 'rate'.")

        return result
    
    def _extract_social_media_info(
        self,
        soup: BeautifulSoup,
        name: str,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract social media links from the soup.

        Args:
            soup: The BeautifulSoup object containing the page.
            name: The project name to check for resemblance.

        Returns:
            A tuple containing Twitter, Telegram, and Website links.
        """
        twitter_link: Optional[str] = None
        telegram_link: Optional[str] = None
        website_link: Optional[str] = None

        divs = soup.find_all("div", class_="flex items-center gap-2.5 text-gray-500 mt-2 justify-center")

        for div in divs:
            links = div.find_all("a")
            for link in links:
                href = link.get("href")
                if "twitter.com" in href or "x.com" in href:
                    twitter_link = href
                elif "t.me" in href or "telegram.me" in href:
                    telegram_link = href
                elif (
                    "discord.com" in href
                    or "facebook.com" in href
                    or "github.com" in href
                    or "reddit.com" in href
                    or "medium.com" in href
                    or "youtube.com" in href
                    or "instagram.com" in href
                ):
                    continue
                else:
                    website_link = href

        return twitter_link, telegram_link, website_link

    def open_sub_url(self, url: str) -> bool:
        """
        Open a sub URL in the driver.

        Args:
            url: The URL to open.

        Returns:
            True if the URL was opened successfully, False otherwise.
        """
        # Set the maximum time to wait for elements to be loaded (in seconds)
        self.driver.set_page_load_timeout(10)

        # Set implicit wait time for elements to be located
        self.driver.implicitly_wait(10)

        try:
            # Attempt to open the URL
            self.driver.get(url)
            time.sleep(10)
            return True
        except Exception as e:
            # Log any exceptions during URL opening
            self.logging.error(f"Failed to open URL: {url}. Exception: {e}")

        return False



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = PinkSaleScrapper(logging)
    status = scraper.start_driver()
    
    if status:
        links = scraper.get_links()
        total = len(links)
        print('Total Links: ', total)
        idx = 0
        for link in links:
            print(link)
            status = scraper.open_sub_url(url=link)
            if status == False:
                continue # Skip to next data
            
            token = scraper.extract_data()
            if token is None:
                continue
            
            print(idx, ' ....................................')
            print("Name: ", token.name)
            print("Symbol: ", token.symbol)
            print("Token Address: ", token.token_address)
            print("Supply: ", token.supply)
            print("Pool Address: ", token.pool_address)
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
            #scraper.extract_token_info(link)

    
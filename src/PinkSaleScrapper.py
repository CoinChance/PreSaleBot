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
        """
        Initialize the PinkSaleScrapper class.

        This function initializes the superclass BaseScrapper with the logging object,
        and sets the base URL for pinksale launchpads.

        Arguments:
            logging: The Python logger to use for logging messages.
        """
        super().__init__(logging)
        self.logging.debug("Initializing the PinkSaleScrapper class.")
        self._url = "https://www.pinksale.finance/launchpads" # Base URL for pinksale launchpads
        self.logging.debug("Set the base URL to %s", self._url)


    def start(self) -> bool:
        """
        Start the scraping process for PinkSale launchpads.

        This function first checks if the webdriver has been initialized
        and if the base URL is accessible. If it is, it opens the URL and
        scrolls down the page to load more data. Then it extracts the links
        from the page source and passes them to the _extract_links() method
        for processing.

        If there is an exception, set the status to False and log the error.

        Returns:
            True if the scraping process was successful, False otherwise.
        """
        super().start_driver()

        try:
            # Check if the webdriver is initialized and the URL is accessible
            if super().get_status():
                # Open the base URL
                super().open_url(self._url)

                # Scroll down to load more data
                for _ in range(self.scroll_downs):
                    # Scroll down by simulating the "END" key press
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                    time.sleep(self.scroll_pause_time)

                # Wait for the page to load
                time.sleep(self.timeout)

                # Set the status to True and extract the links
                self.status = True
                self._extract_links()

            # If there was an exception, set the status to False
            else:
                self.status = False

        # Log the error if there was any exception
        except Exception as ex:
            self.status = False
            self.logging.error("Exception (%s) occured while Opening URL %s", ex, self._url)

        # Return the status of the scraping process
        return self.status



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
                token_info["Chain"] = "Not Available"
                #return None  # If the chain is not found, return None
            else:
                token_info['Chain'] = proj_chain  # Otherwise, set the chain name in the token_info dictionary

            twitter, telegram, website = self._extract_social_media_info(the_soup)
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

        This function finds all divs on the page that contain class "p-2".
        For each div, it checks if it contains the string "Sale live".
        If it does, it extracts all links from that div using the find_all() method.
        If the link href attribute starts with "/launchpad/" or "/solana/launchpad/",
        it constructs a full URL using the domain name and appends it to the list of links.
        It also logs the URL to the log file.

        Returns:
            The total number of links extracted.
        """
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        divs = soup.find_all(class_="p-2")
        links_count = 0
        live_count: int = 0  # Number of live projects
        for div in divs:
            #print('----------------------------------------------')  # Separator
            # Check if the div contains the string "Sale live"
            element = div.find(string='Sale live')
            if element is not None:
                live_count += 1
                links = div.find_all('a')
                #print('Div contains "Sale live" string')
                for link in links:
                    # Extract the href attribute
                    href = link.get('href')
                    #print('href: ', href)
                    if href.startswith('/launchpad/') or href.startswith('/solana/launchpad/'):
                        # Construct a full URL using the domain name
                        link = 'https://www.pinksale.finance' + href
                        self._links.append(link)
                        links_count += 1
                        self.logging.info('URL: %s', link)
            else:
                self.logging.debug('Sale Not Live')
        self.logging.info('Total Live Projects: %d, Scrapped Links: %d', live_count, links_count)
        return links_count

    def _extract_chain(self, label: str, value: str) -> Optional[str]:
        """
        Extract chain from label and value.

        This function first checks if the label contains the string 'Rate' or 'rate'. If it does, it will split the value
        by spaces and store the resulting list in the variable `words`. It then filters out any words that are not in
        the `Chains` array, which is a list of known blockchain names. If exactly one blockchain name is found in the
        value, it is returned as the result.

        Args:
            label: The label to check for 'Rate' or 'rate'.
            value: The value to extract the chain from.

        Returns:
            The chain found in the value or None if no valid chain was found.
        """
        result: Optional[str] = None

        # Check if the label contains 'Rate' or 'rate'
        if 'Rate' in label or 'rate' in label:
            self.logging.debug("The label contains 'Rate' or 'rate'.")

            # Split the value by spaces
            words = value.split()
            self.logging.debug("The value '%s' was split into %s words.", value, words)

            # Filter words that are in the chains_array
            chains = [word for word in words if word in Chains]
            self.logging.debug("Found %s chains in the value: %s", len(chains), chains)

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
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract social media links from the soup.

        This function iterates over all divs with the class "flex items-center
        gap-2.5 text-gray-500 mt-2 justify-center". Inside each div, it finds
        all links and extracts the href attribute from each link. If the href
        attribute contains any of the following strings, the corresponding
        social media link is assigned the href attribute value.

        - "twitter.com" or "x.com" (for Twitter)
        - "t.me" or "telegram.me" (for Telegram)
        - Any other string that is not a subdomain of one of the above

        The function also skips over any links that have href attributes that
        start with '/'. These are likely to be relative links and are not
        useful as standalone links.

        If a link is found that matches one of the above criteria, it is
        assigned to the corresponding variable and the function moves on to the
        next div. If no match is found, the function will not overwrite the
        existing value for that variable. For example, if the function finds a
        Telegram link, it will not overwrite the existing Twitter link if it
        had already found one earlier in the function.

        Once the function has iterated over all divs, it returns a tuple
        containing the extracted links.

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

        twitter_link, telegram_link, website_link = super().social_media(divs)
        # for div in divs:
        #     links = div.find_all("a")
        #     for link in links:
        #         href = link.get("href")
        #         if "twitter.com" in href or "x.com" in href:
        #             if "intent/tweet?" in href:
        #                 continue
        #             twitter_link = href
        #         elif "t.me" in href or "telegram.me" in href:
        #             if "share/msg" in href:
        #                 continue
        #             telegram_link = href
        #         elif (
        #             "discord" in href
        #             or "facebook.com" in href
        #             or "github.com" in href
        #             or "reddit.com" in href
        #             or "medium.com" in href
        #             or "youtube.com" in href
        #             or "instagram.com" in href
        #             or "whatsapp.com" in href
        #             or "linkedin.com" in href
        #         ):
        #             continue
        #         elif href.startswith('/'):
        #             continue
        #         else:
        #             website_link = href

        return twitter_link, telegram_link, website_link


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = PinkSaleScrapper(logging)
    status = scraper.start()
    
    if status:
        links = scraper.get_links()
        total = len(links)
        print('Total Links: ', total)
        idx = 0
        for link in links:
            print(link)
            status = scraper.open_url(url=link)
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
            print("Total Supply: ", token.supply)
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

    
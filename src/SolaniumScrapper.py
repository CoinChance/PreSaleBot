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
from src.Chains import Chains, Alternate_Names


class SolaniumScrapper(BaseScrapper):
    def __init__(self, logging: logging.Logger) -> None:
        """
        Initialize the SolaniumScrapper class.

        This function is the constructor of the class. It is called when an
        instance of the class is created. It initializes the superclass
        BaseScrapper with the logging object, and sets the base URL for
        Solanium launchpads. It also initializes two empty lists to store
        the names and symbols of the Solanium tokens.

        Arguments:
            logging: The Python logger to use for logging messages.
        """
        super().__init__(logging)
        self.logging.debug("Initializing the SolaniumScrapper class.")
        self._url = "https://www.solanium.io/#live-projects"  # Base URL for Solanium launchpads
        self.logging.debug("Set the base URL to %s", self._url)
        self._name: List[str] = []  # List to store the names of Solanium tokens
        self.logging.debug("Initialized the list to store the names of Solanium tokens.")
        #self.symbol: List[str] = []  # List to store the symbols of Solanium tokens
        self.logging.debug("Initialized the list to store the symbols of Solanium tokens.")

    def start(self) -> bool:
        """Start the Selenium webdriver and navigate to the Solanium URL.

        This function is used to start the webdriver and navigate to the Solanium
        URL. It calls the superclass function to start the webdriver, and then
        tries to open the URL. If the open was successful, it scrolls down the
        page to load more data, and then extracts the links from the page.
        It returns True if the URL was opened successfully, and False otherwise.
        """
        super().start_driver()

        try:
            if super().get_status():  # Check if the webdriver is running
                self.logging.debug("Starting to open URL %s", self._url)
                super().open_url(self._url)  # Open the URL

                # Scroll down to load more data                
                self.logging.debug("Scrolling down to load more data")
                for _ in range(self.scroll_downs):  # Scroll down a number of times
                    # Scroll down by simulating the "END" key press
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                    self.logging.debug("Scrolling down (%s/%s)", _ + 1, self.scroll_downs)
                    time.sleep(self.scroll_pause_time)

                self.logging.debug("Waiting for %s seconds before extracting links", self.timeout)
                time.sleep(self.timeout)  # Wait for some time
                self.status = True  # Mark the status as True
                self._extract_links()  # Extract the links from the page

        except Exception as ex:  # Catch any exception that occurs
            self.status = False  # Mark the status as False
            self.logging.error("Exception (%s) occured while Opening URL %s", ex, self._url)  # Log the error

        return self.status  # Return the status
    
    def get_names(self):
        return self._name
    
    @classmethod
    def map_alternate_name(cls, name: str) -> str:
        """Map alternate names to their original names.

        This method is used to map alternate names of Solana chains to their
        original names. The alternate names are stored in the Alternate_Names
        dictionary. The method first converts both the name and the keys of the
        dictionary to lowercase, to make the comparison case-insensitive.
        If the lowercase name is found in the list of lowercase chain names,
        it returns the name as is, as it is already a valid chain name.
        If it's not found, the method iterates over the Alternate_Names
        dictionary and checks if the name matches any of the alternate names.
        If it matches, it returns the original name for that alternate name.
        If it doesn't match any of the alternate names, it returns the name
        as is, as it's not an alternate name, and it's likely a valid chain
        name.
        """
        chains_lower = [chain.lower() for chain in Chains]
        name_lower = name.lower()
        if name_lower in chains_lower:
            return name  # type: ignore

        for alternate_name, original_name in Alternate_Names.items():
            if name == alternate_name:
                return original_name

        return name


    def extract_data(self, name: str) -> Optional[TokenData]:
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
            divs = the_soup.find_all(class_="flex flex-col mb-[30px]")
            for div in divs:
                element = div.find_all(class_="flex justify-between w-full text-sm md:text-md")
                for ele in element:
                    span_elements = ele.find_all('span')
                    try:
                        label = span_elements[0].text.strip()
                        if label is None:
                            continue  # Skip this div if the label is not found
                        
                        value = span_elements[1].text.strip()
                        if value is None:
                            continue  # Skip this div if the value is not found
                        

                        # if label == "Address":
                        #     value = value.split('Do not ')[0].strip()
                        if label == "Chain":
                            value = self.map_alternate_name(value)
                           
                        
                        

                        # Store the label and value in the token_info dictionary
                        token_info[label] = value
                    except Exception as ex:
                        self.logging.error("Error extracting data: %s", ex)

            # if proj_chain is None:
            #     self.logging.error("Chain not found")
            #     return None  # If the chain is not found, return None
            # else:
            #     token_info['Chain'] = proj_chain  # Otherwise, set the chain name in the token_info dictionary
            
            token_info['Name'] = name
            token_info['Status'] = 'Sale live'

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
            return TokenData.solanium_adapter(token_info)  # If there is no error, return the token data
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
        divs = soup.find_all("div", class_="w-full max-w-[580px] shadow-md rounded-solaniumDefault hover:scale-[1.01] hover:shadow-xl transition-all duration-500 bg-white")
        links_count: int = 0  # type: ignore
        live_count: int = 0  # type: ignore
        for div in divs:
            name: Optional[str] = None
            elements = div.find_all("div", class_="content pt-5 px-5 sm:pt-30px sm:px-30px")
            # __name = _div.find_all(class_="block font-poppins-bold text-xl sm:text-[40px]")
            _name_ = elements[0].find_all("span")[0].text.strip()
            if _name_ is not None:
                name = _name_

            #print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")            
            live_count += 1
            links = div.find_all("a")
            #print("----------------------------------------------")
            for link in links:
                # Extract the href attribute
                href = link.get("href")
                #print("href: ", href)
                if href.startswith("/project/"):
                    link = "https://www.solanium.io" + href
                    self._links.append(link)
                    if name is not None:
                        self._name.append(name)
                    name = None
                    links_count += 1
                    self.logging.info("URL: %s", link)

        self.logging.info("Total Live Projects: %d, Scrapped Links: %d", live_count, links_count)
        return links_count

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

        divs = soup.find_all("div", class_="flex flex-col justify-center mb-10 lg:justify-end lg:flex-row px-5 lg:px-0")

        twitter_link, telegram_link, website_link = super().social_media(divs)

        return twitter_link, telegram_link, website_link


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SolaniumScrapper(logging)
    status = scraper.startr()
    
    if status:
        links = scraper.get_links()
        names = scraper.get_names()
        
        total = len(links)
        print('Total Links: ', total)
        idx = 0
        if len(names) == len(links):
            for name, link in zip(names, links):
                status = scraper.open_url(url=link)
                if status == False:
                    continue # Skip to next data
                
                token = scraper.extract_data(name)
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

    
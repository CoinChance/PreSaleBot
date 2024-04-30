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
        super().__init__(logging)
        self._url = "https://www.solanium.io/#live-projects" # Base URL for pinksale launchpads
        self._links: List[str] = [] # List of links scrapped from pinksale launchpads
        self._name: List[str] = []
        self.symbol: List[str] = []
        self.scroll_downs = 10  # Maximum Number of times to scroll down

    def start_driver(self) -> bool:
        super().start_driver()

        try:
            self.driver.get(self._url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(10)

            # Scroll down to load more data
            scroll_pause_time = 2  # type: int
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
        """Open a sub URL in the driver.

        Args:
            url (str): The URL to open.

        Returns:
            bool: True if the URL was opened successfully, False otherwise.
        """
        # Set the maximum time to wait for elements to be loaded (in seconds)
        self.driver.set_page_load_timeout(10)
        # Set implicit wait time for elements to be located
        self.driver.implicitly_wait(10)

        try:
            self.driver.get(url)
            time.sleep(10)
        except Exception as e:
            self.logging.error(f"Failed to open URL: {url}. Exception: {e}")
            return False

        return True

    def get_Status(self):
        return self.status
    
    def get_links(self):
        return self._links
    
    def get_names(self):
        return self._name
    
    @classmethod
    def map_alternate_name(cls, name: str) -> str:
        """Map alternate names to their original names."""
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

            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")            
            live_count += 1
            links = div.find_all("a")
            print("----------------------------------------------")
            for link in links:
                # Extract the href attribute
                href = link.get("href")
                print("href: ", href)
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

        for div in divs:
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
                else:
                    if href.startswith('/'):
                        continue
                    website_link = href  # type: ignore

        return twitter_link, telegram_link, website_link


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SolaniumScrapper(logging)
    status = scraper.start_driver()
    
    if status:
        links = scraper.get_links()
        names = scraper.get_names()
        
        total = len(links)
        print('Total Links: ', total)
        idx = 0
        if len(names) == len(links):
            for name, link in zip(names, links):
                status = scraper.open_sub_url(url=link)
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

    
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


class DxSaleScrapper(BaseScrapper):
    def __init__(self, logging: logging.Logger) -> None:  
        """
        Initialize the DxSaleScrapper class.

        This function initializes the superclass BaseScrapper with the logging object,
        and sets the base URL for DxSale launchpads.

        Arguments:
            logging: The Python logger to use for logging messages.
        """
        super().__init__(logging)      
        self._url = "https://www.dx.app/dxsale" # Base URL for DxSale launchpads
        self.logging.debug("Set the base URL to %s", self._url)

    def start(self) -> bool:
        """
        Starts the Selenium driver, opens the DxSale website, and extracts links.
        
        This function returns True if the operation was successful, and False otherwise.
        If there is an exception, the function logs the error and returns False.
        """
        super().start_driver()    
           
        try:
            # Check if the driver is running
            if super().get_status():
                # Open the DxSale website
                super().open_url(self._url)
                # Extract links from the page
                self._extract_links()
        except Exception as ex:
            # If there is an exception, log it and set the status to False
            self.status = False
            self.logging.error("Exception (%s) occured while Opening URL %s", ex, self._url)

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
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            token_info: Dict[str, str] = {}  # The dictionary to store all the token data

            # Name
            try:
                name_element = soup.find('h1', class_='MuiTypography-root MuiTypography-h3 css-vwfc3z')
                if name_element:
                    name = name_element.text
                    if name:
                        token_info["Name"] = name
            except Exception as ex:
                self.logging.error("Exception (%s) occured while extracting Name", ex)

            # Symbol
            try:
                symbol_element = soup.find('h2', class_='MuiTypography-root MuiTypography-h6 css-eezjbm')
                if symbol_element:
                    symbol = symbol_element.text
                    if symbol:
                        token_info["Symbol"] = symbol
            except Exception as ex:
                self.logging.error("Exception (%s) occured while extracting Symbol", ex)

            # Raised
            try:
                raised_info = soup.find('p', class_='MuiTypography-root MuiTypography-h5 css-oh7pm8')
                if raised_info:
                    token_info["Raised"] = raised_info.text
            except Exception as ex:
                self.logging.error("Exception (%s) occured while extracting Raised", ex)

            desired_tags = ["Presale address", "Token address", "Soft Cap", "Total Supply"]
            # Presale Address
            for tag in desired_tags:
                try:
                    presale_address_label = soup.find('span', string=tag)
                    if presale_address_label:
                        presale_address_value = presale_address_label.find_next('span', class_='MuiTypography-subtitle2')
                        if presale_address_value:
                            token_info[tag] = presale_address_value.text # Extract Presale Address
                except Exception as ex:
                    self.logging.error("Exception (%s) occured while extracting Presale Address", ex)

            token_info['Chain'] = 'DEX'
            token_info['Status'] = "Sale live"
            twitter, telegram, website = self._extract_social_media_info(soup)
            if twitter is None:
                token_info['Twitter'] = "Not Available"  # If the Twitter link is not found, set the Twitter key to "Not Available"
            else:
                token_info['Twitter'] = twitter  # Otherwise, set the Twitter key to the Twitter link

            if telegram is None:
                token_info['Telegram'] = "Not Available"  # If the Telegram link is not found, set the Telegram key to "Not Available"
            else:
                token_info['Telegram'] = telegram  # Otherwise, set the Telegram key to the Telegram link

            if website is None:
                token_info['Website'] = "Not Available"  # If the website link is not found, set the website key to "Not Available"
            else:
                token_info['Website'] = website  # Otherwise, set the website key to the website link

            # Adapt the dictionary to TokenData class
            return TokenData.dexsale_adapter(token_info)  # If there is no error, return the token data
        except Exception as e:
            self.logging.error("Error: %s", e)
            return None  # If there is an error, return None

    def _extract_links(self) -> int:
        """
        Extract links from PinkSale website.

        Returns:
            The total number of links extracted.
        """

        divs = self.driver.find_elements(By.CLASS_NAME, "MuiGrid-root MuiGrid-container MuiGrid-item MuiGrid-spacing-xs-1 css-184a75u")
        # Find the dropdown element by its ID, name, XPath, or CSS selector
        dropdown_element = WebDriverWait(self.driver, self.timeout).until(EC.visibility_of_element_located((By.XPATH, "//label[contains(text(), 'Filter by')]/following-sibling::div")))
        dropdown_element.click()

        dropdown_items = WebDriverWait(self.driver, self.timeout).until(EC.visibility_of_all_elements_located((By.XPATH, "//ul[@role='listbox']/li[@role='option']")))
        for item in dropdown_items:
            if item.text.strip() == 'Running':
                item.click()
                break
        
        time.sleep(self.timeout)

        
        for _ in range(self.scroll_downs):
            # Scroll down by simulating the "END" key press
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(self.scroll_pause_time)
        time.sleep(self.timeout)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        divs = soup.find_all(class_="MuiPaper-root MuiPaper-elevation MuiPaper-rounded MuiPaper-elevation2 MuiCard-root p-0 relative w-full max-w-[350px] rounded-lg css-1vpe3e2")
        links_count = 0
        live_count = 0
        for div in divs:
            #print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
            # Find all links in the div
            
            live_count += 1
            links = div.find_all('a')
            #print('----------------------------------------------')
            for link in links:
                # Extract the href attribute
                href = link.get('href')
                #print('href: ', href)
                if href.startswith('/dxsale/'):
                    link = "https://www.dx.app" + href
                    self._links.append(link)
                    links_count += 1
                    self.logging.info('URL: %s', link)
            
        self.logging.info('Total Live Projects: %d, Scrapped Links: %d' , live_count, links_count)
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
        soup: BeautifulSoup,  # The BeautifulSoup object containing the page.
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract social media links from the soup.

        This function searches for all the div elements with the class name 'MuiBox-root css-qokrjo' and iterates
        through each of those div elements. It then finds all the anchor elements within each div and extracts the
        href attribute from each anchor element. If the href attribute contains any of the social media websites
        such as Twitter, Telegram, or the Website, it stores the href in the appropriate variable.

        The variables are:
            twitter_link: The href attribute of the Twitter link.
            telegram_link: The href attribute of the Telegram link.
            website_link: The href attribute of the Website link.

        This function ignores links that contain the following:
            - Any social media website link with "share/msg" in the link.
            - Any link that starts with a forward slash '/'.
            - Any link that contains "intent/tweet?" in the link, this is a Twitter specific link.
            - The website "x.com" which is not a real domain.
            - The website "discord.com", "facebook.com", "github.com", "reddit.com", "medium.com", "youtube.com",
              "instagram.com", "whatsapp.com", or "linkedin.com".

        Args:
            soup: The BeautifulSoup object containing the page.

        Returns:
            A tuple containing Twitter, Telegram, and Website links.
        """
        twitter_link: Optional[str] = None
        telegram_link: Optional[str] = None
        website_link: Optional[str] = None

        divs = soup.find_all("div", class_="MuiBox-root css-qokrjo")

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
        #         else:
        #             if href.startswith('/'):
        #                 continue
        #             website_link = href

        return twitter_link, telegram_link, website_link


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = DxSaleScrapper(logging)
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


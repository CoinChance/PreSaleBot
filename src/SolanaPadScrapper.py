

import time
import logging
from typing import Optional, Dict, Tuple, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

from TokenData import TokenData
from BaseScrapper import BaseScrapper
from Chains import Chains

class SolanaPadScrapper(BaseScrapper):
    def __init__(self, logging: logging.Logger) -> None:
        super().__init__(logging)
        self._url: str = "https://solanapad.io/launchpad-list"  # type: ignore
        self._links: List[str] = []  # type: ignore
        self.scroll_downs: int = 10
      
             

    def start_driver(self) -> bool:
        """Start the Selenium driver and return its status."""
        super().start_driver()

        try:
            self.driver.get(self._url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(10)

            live_menu = self.driver.find_element(By.XPATH, "//li[contains(@data-menu-id, 'live')]")
            live_menu.click()

            time.sleep(10)
            # Scroll down to load more data
            # scroll_pause_time = 5  # Adjust as needed

            for _ in range(self.scroll_downs):
                # Scroll down by simulating the "END" key press
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                time.sleep(5)

            time.sleep(5)
            self.status = True
            self._extract_links()

        except Exception as ex:
            self.status = False
            self.logging.error("Exception (%s) occured while Opening URL %s", ex, self._url)

        return self.status
    
    def _extract_links(self) -> int:
        """
        Extract links from PinkSale website.

        Returns:
            The total number of links extracted.
        """
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        divs = soup.find_all("div", class_="py-5 px-3 lg:p-6 bg-[#18182B] rounded-2xl flex flex-col gap-4 text-base")
        links_count = 0
        live_count = 0
        for div in divs:
            element = div.find(string='View more')
            if element is None:
                continue
            live_count += 1
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
            links = div.find_all('a')
            # Find all links in the div
            for link in links:
                # Extract the href attribute
                href = link.get('href')
                print('href: ', href)
                if href.startswith('/launchpad-list/'):
                    link = 'https://solanapad.io' + href
                    self._links.append(link)
                    links_count += 1
                    self.logging.info('URL: %s', link)
                    break
            
        self.logging.info('Total Live Projects: %d, Scrapped Links: %d' , live_count, links_count)
        return links_count


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

        return name, twitter_link, telegram_link, website_link

    def _extract_total_supply(self):
        # Find the element you want to hover over
        element = self.driver.find_element_by_xpath("//canvas[@class='text-xl']")

        # Create an ActionChains object
        action_chains = ActionChains(self.driver)

        # Move the mouse to the element
        action_chains.move_to_element(element).perform()
        
        tooltip = WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='tooltip']")))

        # Extract the tooltip text
        tooltip_text = tooltip.text

    def extract_data(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            proj_chain: Optional[str] = None  # The chain name for the project
            token_info: Dict[str, str] = {}  # The dictionary to store all the token data
            
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
    
    def extract_token_info_strategy1(self, url):

        super().start_driver()
        # status, live_status = self.open_sub_url(url=url, xpath="/html/body/div/div/div[3]/main/div/div/div[2]/div[2]/div[1]/div[3]/div[2]/div[2]")
        
        # if status == False:
        #     return data
        
        data = TokenData()
        try:            
            self.sec_driver.get(url)
            self.sec_driver.implicitly_wait(10)           
            status = True
        except Exception as ex:
            status = False
            self.logging.error("Exception (%s) occured while Opening URL %s", ex, url)

        if status == True:
            
            data.status = True
            data.symbol = super().extract_data(tag='Symbol', xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/h3", extract_type='text')                
            data.live_status = super().extract_data(tag='Live Status', xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/div[2]/div[2]/span", extract_type='text')
            data.web = super().extract_data(tag='URL', xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[2]/div/a[1]", extract_type='url')
            data.twitter = super().extract_data(tag='Twitter', xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[2]/div/a[2]", extract_type='url')
            data.telegram = super().extract_data(tag='Telegram', xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[2]/div/a[3]", extract_type='url')
           
            data.rate       = super().extract_data(tag="Current Rate\n",      xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[2]/ul/li[1]", extract_type='text').split('\n')[1]
            data.start_time  = super().extract_data(tag="Start Time\n", xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[2]/ul/li[2]", extract_type='text').split('\n')[1]
            data.end_time    = super().extract_data(tag="End Time\n",   xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[2]/ul/li[3]", extract_type='text').split('\n')[1]
            data.soft_cap    = super().extract_data(tag="Soft Cap\n",   xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[2]/ul/li[4]", extract_type='text').split('\n')[1]
            
            data.raised = super().extract_data(tag="\n", xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[2]/div/div[2]/div[3]/div/div/span[1]", extract_type='text_split').split('\n')[0]   
            data.token_address = super().extract_data(tag="Token Address\n", xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[2]/ul/li[9]/div/span[1]", extract_type='text')
            data.pool_address = super().extract_data(tag="Pool Address\n", xpath="/html/body/div/div[1]/div[2]/main/div/div[2]/div[2]/div[1]/div[2]/ul/li[10]/div/span[1]", extract_type='text')
        return data
            
    def get_Status(self):
        return self.status
    
    def get_links(self):
        return self._links



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
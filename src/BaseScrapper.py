
import time
import logging
from bs4.element import Tag
from selenium import webdriver

from selenium.webdriver.common.by import By
from typing import Optional, Dict, Tuple, List
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.firefox.service import Service

class BaseScrapper:
    def __init__(self, logging: logging.Logger) -> None:
        """
        Initialize the BaseScrapper.

        This function will initialize the private variables for the class
        which are used to keep track of the Selenium driver, the status of
        the driver, the list of links to be scraped, and the logger. It also
        sets the number of times to scroll down to load more data.

        Arguments:
            logging: The Python logger to use for logging messages.
        """
        self.driver: Optional[webdriver.Firefox] = None  # The Selenium driver (a web browser). Initially set to None.
        self.status: Optional[bool] = None  # The status of the Selenium driver. Initially set to None.
        self._links: List[str] = []  # A list of links to be scraped. Initially an empty list.
        self.logging = logging  # The Python logger to use for logging messages.
        self.scroll_downs = 10  # The number of times to scroll down to load more data.
        self.scroll_pause_time = 5
        self.timeout = 40  # The number of seconds to wait for an element to appear on the page.

    def start_driver(self) -> None:
        """
        Start the Selenium driver and return its status.

        This function will start the Selenium driver (which will launch a new
        web browser in headless mode), set the status to True, and log a
        message indicating that the driver has been successfully connected
        to the website.

        Arguments:
            None

        Returns:
            None
        """
        if self.status is None:
            # Set firefox options to run in headless mode
            options = webdriver.FirefoxOptions()
            options.add_argument('--no-sandbox')  # Required for running in Docker
            options.add_argument('--disable-dev-shm-usage')  # Required for running in Docker
            options.add_argument('--headless')  # Run in headless mode

            # Initialize the Selenium driver (which will launch a new web browser)
            # We need to explicitly tell Python what type of object to expect
            # because we're ignoring the type check for the driver argument
            self.driver = webdriver.Firefox(  # type: ignore[no-untyped-call]
                service=Service(GeckoDriverManager().install()), options=options)

            # Log a message indicating that the driver has been successfully
            # connected to the website
            self.logging.info("Selenium successfully connected to the website")

            # Set the status to True
            self.status = True

    def open_url(self, url: str) -> bool:
            """
            Open a sub URL in the driver.

            Args:
                url: The URL to open.

            Returns:
                True if the URL was opened successfully, False otherwise.
            """
            # Set the maximum time to wait for elements to be loaded (in seconds)
            self.driver.set_page_load_timeout(self.timeout)

            # Set implicit wait time for elements to be located
            self.driver.implicitly_wait(self.timeout)

            try:
                # Attempt to open the URL
                self.driver.get(url)
                time.sleep(self.timeout)
                return True
            except Exception as e:
                # Log any exceptions during URL opening
                self.logging.error(f"Failed to open URL: {url}. Exception: {e}")

            return False

    def get_status(self) -> Optional[bool]:
        """Return the status of the Selenium driver."""
        return self.status

    def get_links(self):
        """Return the links scrapped by the Selenium driver."""
        return self._links
    
    def social_media(self, divs: List[Tag]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        twitter_link: Optional[str] = None
        telegram_link: Optional[str] = None
        website_link: Optional[str] = None

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
                elif any(
                    website in href
                    for website in (
                        "discord",
                        "facebook.com",
                        "github.com",
                        "reddit.com",
                        "medium.com",
                        "youtube.com",
                        "instagram.com",
                        "whatsapp.com",
                        "linkedin.com",
                    )
                ):
                    continue
                elif href.startswith('/'):
                    continue
                else:
                    website_link = href

        return twitter_link, telegram_link, website_link


    def stop_driver(self) -> None:
        """
        Cleanup the Selenium driver.

        This function will quit the Selenium driver (which will close the
        web browser), set the status to None, clear the list of links, and
        log a message indicating that the driver has been successfully
        disconnected from the website.
        """
        if self.status is True:
            self.driver.quit()  # type: ignore
            # Quit the Selenium driver, which will close the web browser
            self.status = None
            # Set the status to None, indicating that the driver is now closed
            self._links.clear()
            # Clear the list of links to free up memory
            self.logging.info("Selenium successfully disconnected from the website")
            # Log a message indicating that the driver has been successfully
            # disconnected from the website

    def extract_data(self,
                     tag: str,  # The name of the data being extracted
                     xpath: str,  # The XPATH to the data in the web page
                     extract_type: str = 'text') -> Optional[str]:  # The type of data to extract
        """
        Extract data from the web page based on the given XPATH.

        The function will return the extracted data if successful, or None if something fails.
        The function also logs the error so that it can be easily debugged.

        Arguments:
            tag: The name of the data being extracted
            xpath: The XPATH to the data in the web page
            extract_type: The type of data to extract. Valid values are:
                'text': Get the text inside the element
                'text_split': Get the first line of text inside the element
                'url': Get the URL of the element

        Returns:
            The extracted data, or None if something fails
        """
        if self.status is False:
            return None  # If the driver is not connected, return None

        try:
            element: Optional[WebElement] = self.driver.find_element(By.XPATH, xpath)
            if extract_type == 'text':
                return element.text.strip() if element else None  # Extract the text and return it
            elif extract_type == 'text_split':
                return element.text.strip().split('\n')[0] if element else None  # Extract the first line of text and return it
            elif extract_type == 'url':
                return element.get_attribute('href') if element else None  # Extract the URL attribute of the element
            else:
                raise ValueError(f"Unknown extract type: {extract_type} at tag: {tag}")  # Log an error if the extract type is not recognized
        except Exception as e:
            self.logging.error(f"Error: {e} at tag: {tag}")  # Log the error
            return None  # Return None if something fails

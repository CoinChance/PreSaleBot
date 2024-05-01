
import logging
import schedule
from bs4.element import Tag
from typing import Optional, Dict, Tuple, List
from src.PinkSaleScrapper import PinkSaleScrapper
from src.SolanaPadScrapper import SolanaPadScrapper
from src.SolaniumScrapper import SolaniumScrapper
from src.DxSaleScrapper import DxSaleScrapper
from src.TokenData import TokenData
from src.Database import Database

class Scheduler:
    def __init__(self, logging_: logging.Logger, db_: Database) -> None:
        """
        Initialize the Scheduler class.

        This function initializes the logger and the database for the scheduler.

        Arguments:
            logging_: The Python logger to use for logging messages.
            db_: The instance of the Database class to use.
        """
        self.db = db_
        self.logging = logging_

        # Set up scraper
        self.pinksale = PinkSaleScrapper(logging=logging_)
        self.solanapad = SolanaPadScrapper(logging=logging_)
        self.solanium = SolaniumScrapper(logging=logging_)
        self.dxsale = DxSaleScrapper(logging=logging_)

    def pinksale_job(self) -> None:
        """
        Start PinkSale job

        This function will start the PinkSale scrapper, open a list of links, scrape
        the data for each link, check if the project is already in the database,
        and if not, insert the data into the database.

        Steps:
        """
        status = self.pinksale.start_driver()

        if status:
            links = self.pinksale.get_links()
            for proj_url in links:
                if self.db.check_project_url(proj_url) is False:
                    self.logging.info('Project seems to be new, Scrapping URL: %s', proj_url)
                    try:
                        self.pinksale.open_url(url=proj_url)
                        data = self.pinksale.extract_data()
                        if data.live_status is True and data.status is True:
                            self.logging.info('Project is Live, Add Info to DB: %s', proj_url)
                            self.db.insert_project_data(proj_url, data)
                        else:
                            self.logging.info('Project is not LIVE, Skipping URL: %s', proj_url)
                    except Exception as e:
                        self.logging.info('Exception while Srcapping, Skipping URL: %s', proj_url)
                        self.logging.error(e)
                else:
                    self.logging.info('Project already exists, Skipping URL: %s', proj_url)
        else:
            self.logging.error("Failed to Initialize scrapper for PinkSale")

        if self.pinksale.get_status():
            self.pinksale.stop_driver()

    def solanapad_job(self) -> None:
        """
        Start SolanaPad job

        This function will start the SolanaPad scrapper, open a list of links, scrape
        the data for each link, check if the project is already in the database,
        and if not, insert the data into the database.

        Steps:

        1. Start the SolanaPad scrapper driver
        2. Get a list of project URLs from SolanaPad
        3. Iterate over each project URL
        4. Check if the project is already in the database
        5. If the project is new, open the project URL using the SolanaPad driver
        6. Extract the data for the project from the SolanaPad page
        7. Check if the project is live and has a status of True
        8. If the project is live and has a status of True, insert the data into the database
        9. If there is an exception while scraping, log it and skip the project
        10. Stop the SolanaPad scrapper driver
        """
        # Start the SolanaPad scrapper driver
        status: bool = self.solanapad.start_driver()

        if status:
            # Get a list of links from SolanaPad
            links: List[str] = self.solanapad.get_links()

            # Iterate over each link
            for proj_url in links:
                # Check if the project is already in the database
                if self.db.check_project_url(proj_url) is False:
                    self.logging.info('Project seems to be new, Scrapping URL: %s', proj_url)

                    try:
                        # Open the URL using the SolanaPad driver
                        self.solanapad.open_url(url=proj_url)

                        # Extract the data from the SolanaPad page
                        data: TokenData = self.solanapad.extract_data()

                        # Check if the project is live and has a status of True
                        if data.live_status is True and data.status is True:
                            self.logging.info('Project is Live, Add Info to DB: %s', proj_url)

                            # Insert the data into the database for this project
                            self.db.insert_project_data(proj_url, data)

                        else:
                            self.logging.info('Project is not LIVE, Skipping URL: %s', proj_url)

                    except Exception as e:
                        self.logging.info('Exception while Srcapping, Skipping URL: %s', proj_url)
                        self.logging.error(e)

                else:
                    self.logging.info('Project already exists, Skipping URL: %s', proj_url)

        else:
            self.logging.error("Failed to Initialize scrapper for SolanaPad")

        if self.solanapad.get_status():
            self.solanapad.stop_driver()


    def solanium_job(self) -> None:
        """
        Start Solanium job

        This function will start the Solanium scrapper, open a list of links, scrape
        the data for each link, check if the project is already in the database,
        and if not, insert the data into the database.

        Steps:
        1. Start Solanium scrapper
        2. Get list of links from Solanium driver
        3. For each URL in the list:
            3.1. Check if the project is already in the database
            3.2. If not in database, scrape project data using Solanium
            3.3. If the project is live (live_status == True) and not archived (status == True),
                insert the data into the database
            3.4. If there is an exception, log the exception and skip the project
        """
        # Start the Solanium scrapper
        status: bool = self.solanium.start_driver()

        if status:  # type: ignore
            # Get list of links from Solanium driver
            links: List[str] = self.solanium.get_links()
            # Get list of names from Solanium driver
            names: List[str] = self.solanium.get_links()
            # If the length of the names list is equal to the length of the links list,
            # we can proceed with the scraping
            if len(names) == len(links):
                for name, proj_url in zip(names, links):
                    # Check if the project is already in the database
                    if self.db.check_project_url(proj_url) is False:
                        self.logging.info('Project seems to be new, Scrapping URL: %s', proj_url)
                        try:
                            # Open the URL using Solanium
                            self.solanium.open_url(url=proj_url)
                            # Extract the data from the page using Solanium
                            data: TokenData = self.solanium.extract_data(name)
                            # Check if the project is live (live_status == True) and not
                            # archived (status == True)
                            if data.live_status and data.status:
                                self.logging.info('Project is Live, Add Info to DB: %s', proj_url)
                                # Insert data into the database
                                self.db.insert_project_data(proj_url, data)
                            else:
                                self.logging.info('Project is not LIVE, Skipping URL: %s', proj_url)
                        except Exception as e:
                            self.logging.info('Exception while Srcapping, Skipping URL: %s', proj_url)
                            self.logging.error(e)
                    else:
                        self.logging.info('Project already exists, Skipping URL: %s', proj_url)

        else:
            self.logging.error("Failed to Initialize scrapper for Selenium")

        if self.solanium.get_status():
            self.solanium.stop_driver()
            
    def dxsale_job(self) -> None:
        """
        Start DxSale job

        This function will start the DxSale scrapper, open a list of links, scrape
        the data for each link, check if the project is already in the database,
        and if not, insert the data into the database.
        """
        # Start the DxSale scrapper
        status: bool = self.dxsale.start()
        
        if status:     
            # Get a list of links from DxSale
            links: List[str] = self.dxsale.get_links()
            # Iterate over each link
            for proj_url in links:
                # Check if the project is already in the database
                if self.db.check_project_url(proj_url) == False:   
                    self.logging.info('Project seems to be new, Scrapping URL: %s', proj_url)  
                    try:
                        # Open the URL using the DxSale driver
                        self.dxsale.open_url(url=proj_url)
                        # Extract the data from the DxSale page
                        data: TokenData = self.dxsale.extract_data()
                        # Check if the project is live and has a status of True
                        if data.live_status == True and data.status == True:
                            self.logging.info('Project is Live, Add Info to DB: %s', proj_url)
                            # Insert the data into the database for this project
                            self.db.insert_project_data(proj_url, data)
                        else:
                            self.logging.info('Project is not LIVE, Skipping URL: %s', proj_url)
                    except Exception as e:
                        self.logging.info('Exception while Srcapping, Skipping URL: %s', proj_url)
                        self.logging.error(e)
                else:
                    self.logging.info('Project already exists, Skipping URL: %s', proj_url)
            
        else:
            self.logging.error("Failed to Initialize scrapper for DxSale")

        if self.dxsale.get_status():
            self.dxsale.stop_driver()

          

    def run(self) -> None:
        """
        This function will run the scheduler, which will execute the job for each
        platform.

        The function will log if an error occurs, and if so, the error will be
        printed to the console.

        The function will also close the database connection when it's done
        running.
        """
        try:
            self.logging.info("Starting Scheduler")
            # Connect to the database
            self.db.connect()
            self.logging.info("DB Connected")

            self.logging.info("Starting DxSale Job")
            # Run the DxSale job
            self.dxsale_job()
            self.logging.info('')

            self.logging.info("Starting Selenium Job")
            # Run the Solanium job
            self.solanium_job()
            self.logging.info('')

            self.logging.info("Starting SolanaPad Job")
            # Run the SolanaPad job
            self.solanapad_job()
            self.logging.info('')

            self.logging.info("Starting Pinksale Job")
            # Run the PinkSale job
            self.pinksale_job()
            self.logging.info('')

        except Exception as e:
            # If there's an error, log it
            self.logging.error("Error occurred: %s", e)
            # Print the error to the console
            print(e)

        finally:
            # Close the database connection
            self.db.close()
            self.logging.info("DB Connection Closed")
            self.logging.info('Scheduler Stopped')
            self.logging.info('.......................')
            self.logging.info('')
            
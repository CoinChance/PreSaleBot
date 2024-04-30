
import logging
import schedule
from src.PinkSaleScrapper import PinkSaleScrapper
from src.SolanaPadScrapper import SolanaPadScrapper
from src.SolaniumScrapper import SolaniumScrapper
from src.DxSaleScrapper import DxSaleScrapper

class Scheduler:
    def __init__(self, logging, db):
        self.db = db
        self.logging = logging
        # Set up scraper
        self.pinksale = PinkSaleScrapper(logging=logging)
        self.solanapad = SolanaPadScrapper(logging=logging)
        self.solanium = SolaniumScrapper(logging=logging)
        self.dxsale = DxSaleScrapper(logging=logging)

        #self.urls_file = urls_file

    def pinksale_job(self):
        #for url in urls:
        status = self.pinksale.start_driver()
        
        if status:     
            links = self.pinksale.get_links()
            for proj_url in links:                    
                #proj_url = link.get_attribute('href')
                #logging.info('URL: %s', link.get_attribute('href'))  # Print the href attribute value of each <a> tag
                if self.db.check_project_url(proj_url) == False:   
                    self.logging.info('Project seems to be new, Scrapping URL: %s', proj_url)  
                    try:
                        self.pinksale.open_sub_url(url=proj_url)                    
                        #data = self.pinksale.extract_token_info(proj_url=proj_url)
                        data = self.pinksale.extract_data()
                        if data.live_status == True and data.status == True:
                            self.logging.info('Project is Live, Add Info to DB: %s', proj_url)
                            self.db.insert_project_data(proj_url, data)
                            continue
                        else:
                            self.logging.info('Project is not LIVE, Skipping URL: %s', proj_url)
                    except Exception as e:
                        self.logging.info('Exception while Srcapping, Skipping URL: %s', proj_url)
                        self.logging.error(e)
                else:
                    self.logging.info('Project already exists, Skipping URL: %s', proj_url)
            
        else:
            self.logging.error("Failed to Initialize scrapper for PinkSale")

        if self.pinksale.get_Status():
            self.pinksale.stop_driver()

    def solanapad_job(self):
        #for url in urls:
        status = self.solanapad.start_driver()
        
        if status:     
            links = self.solanapad.get_links()
            for proj_url in links:     
                if self.db.check_project_url(proj_url) == False:   
                    self.logging.info('Project seems to be new, Scrapping URL: %s', proj_url)    
                    try:
                        self.solanapad.open_sub_url(url=proj_url)          
                        data = self.solanapad.extract_data()
                        if data.live_status == True and data.status == True:
                            self.logging.info('Project is Live, Add Info to DB: %s', proj_url)
                            self.db.insert_project_data(proj_url, data)
                            continue
                        else:
                            self.logging.info('Project is not LIVE, Skipping URL: %s', proj_url)
                    except Exception as e:
                        self.logging.info('Exception while Srcapping, Skipping URL: %s', proj_url)
                        self.logging.error(e)
                else:
                    self.logging.info('Project already exists, Skipping URL: %s', proj_url)
            
        else:
            logging.error("Failed to Initialize scrapper for SolanaPad")

        if self.solanapad.get_Status():
            self.solanapad.stop_driver()

    def solanium_job(self):
        #for url in urls:
        status = self.solanium.start_driver()
        
        if status:     
            links = self.solanium.get_links()
            names = self.solanium.get_links()
            if len(names) == len(links):
                for name, proj_url in zip(names, links):    
                    if self.db.check_project_url(proj_url) == False:   
                        self.logging.info('Project seems to be new, Scrapping URL: %s', proj_url)    
                        try:
                            self.solanium.open_sub_url(url=proj_url)          
                            data = self.solanium.extract_data(name)
                            if data.live_status == True and data.status == True:
                                self.logging.info('Project is Live, Add Info to DB: %s', proj_url)
                                self.db.insert_project_data(proj_url, data)
                                continue
                            else:
                                self.logging.info('Project is not LIVE, Skipping URL: %s', proj_url)
                        except Exception as e:
                            self.logging.info('Exception while Srcapping, Skipping URL: %s', proj_url)
                            self.logging.error(e)
                    else:
                        self.logging.info('Project already exists, Skipping URL: %s', proj_url)
            
        else:
            logging.error("Failed to Initialize scrapper for Selenium")

        if self.solanium.get_Status():
            self.solanium.stop_driver()
            
    def dxsale_job(self):
        #for url in urls:
        status = self.dxsale.start_driver()
        
        if status:     
            links = self.dxsale.get_links()
            for proj_url in links:                    
                #proj_url = link.get_attribute('href')
                #logging.info('URL: %s', link.get_attribute('href'))  # Print the href attribute value of each <a> tag
                if self.db.check_project_url(proj_url) == False:   
                    self.logging.info('Project seems to be new, Scrapping URL: %s', proj_url)  
                    try:
                        self.dxsale.open_sub_url(url=proj_url)                    
                        #data = self.pinksale.extract_token_info(proj_url=proj_url)
                        data = self.dxsale.extract_data()
                        if data.live_status == True and data.status == True:
                            self.logging.info('Project is Live, Add Info to DB: %s', proj_url)
                            self.db.insert_project_data(proj_url, data)
                            continue
                        else:
                            self.logging.info('Project is not LIVE, Skipping URL: %s', proj_url)
                    except Exception as e:
                        self.logging.info('Exception while Srcapping, Skipping URL: %s', proj_url)
                        self.logging.error(e)
                else:
                    self.logging.info('Project already exists, Skipping URL: %s', proj_url)
            
        else:
            self.logging.error("Failed to Initialize scrapper for DxSale")

        if self.dxsale.get_Status():
            self.dxsale.stop_driver()

          

    def run(self):
        try:
            self.logging.info("Starting Scheduler")
            self.db.connect()
            self.logging.info("DB Connected")

            self.logging.info("Starting DxSale Job")
            self.dxsale_job()
 
            self.logging.info("Starting Solanium Job")
            self.solanium_job()

            self.logging.info("Starting SolanaPad Job")
            self.solanapad_job()

            self.logging.info("Starting PinkSale Job")
            self.pinksale_job()


        except Exception as e:
            self.logging.error("Error occurred: %s", e)

        finally:
            self.db.close()
            
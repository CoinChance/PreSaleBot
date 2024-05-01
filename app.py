
import os
import time
import logging
import schedule
import datetime
from src.Database import Database
from src.Scheduler import Scheduler
from typing import Optional, Dict, Tuple, List
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

 # Get the value of the environment variables
DELETE_FILES_OLDER_THAN_DAYS = int(os.environ.get('DELETE_FILES_OLDER_THAN_DAYS', '30'))        # default 30
DELETE_SERVICE_INTERVAL=int(os.environ.get('DELETE_SERVICE_INTERVAL', '12'))        # default 12
SCRAPPING_INTERVAL=int(os.environ.get('SCRAPPING_INTERVAL', '1'))        # default 12
HOST = os.environ.get('DB_HOST', 'localhost')
DB_DATABASE = os.environ.get('DB_DATABASE', 'presalebot')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'presalebot')
PORT = os.environ.get('PORT', '5432')




def config_log() -> logging.Logger: # type: ignore
    """Configure logging

    This function creates a logging directory if it does not exist. The
    function then uses the current datetime to create a new log file. The
    full path to the log file is created and returned.

    The function then creates a logger and sets its log level to INFO.
    It also creates a file handler which is responsible for writing logs
    to the log file. The FileHandler is passed a formatter, which formats
    the log messages as "%(asctime)s - %(levelname)s - %(message)s"

    Finally, the FileHandler is added to the logger and a log message is
    emitted indicating that the log file was created successfully.

    The logger is returned from the function so it can be used in the
    application.

    Returns:
        logging.Logger: The configured logger
    """
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Create the full path to the log file
    formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filepath = os.path.join(log_directory, f"log_{formatted_datetime}.txt")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_filepath)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.info("Log File Created Successfully")
    return logger

logging = config_log()

def config_db(    
) -> Optional[Database]:
    """Configure database connection and return Database object if successful

    This function first creates the directory "db" if it does not exist.

    Next, it sets up the database connection by creating a Database object
    and passing in the necessary parameters.

    The function then calls the connect() method on the Database object to
    establish a connection to the database. If the connection was not
    successful, the function logs an error message and returns None.

    If the connection was successful, the function returns the Database
    object.

    Returns:
        Optional[Database]: The Database object if connection was successful,
                            otherwise None
    """
    db_directory = "db"
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)

    # Set up database connection
    db = Database(
        logging=logging,
        host=HOST,
        port=PORT,
        database=DB_DATABASE,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    status = db.connect()
    if not status:
        logging.error("Error connecting to database")
        return None
    return db


def delete_old_logs() -> None:
    """Delete old log files

    This function deletes log files that are older than DELETE_FILES_OLDER_THAN_DAYS days.
    The log files are stored in the "logs" directory.

    The function first gets the current date and time using the datetime module.

    Next, the function defines the directory containing the log files.

    The function then gets the list of files in the directory.

    The function then iterates over the list of files and checks if each file is a regular file.

    If a file is a regular file, the function tries to get its creation time using the os.path.getctime() function.
    If this function call is successful, the function calculates the difference in days between the current date
    and the creation time of the file.

    If the difference in days is greater than DELETE_FILES_OLDER_THAN_DAYS, the file is deleted.

    If the function is unable to get the creation time of a file, it logs an error message.

    After iterating over all the files, the function logs a message indicating that the function has finished.

    """
    if logger is None:
        logger = logging.getLogger(__name__)
    # Log a separator to make it easier to read the logs
    logger.info('........................................................')
    # Log a message indicating the start of the function
    logger.info('............Delete Log Scheduler........................')
    # Get current date
    current_date: datetime.datetime = datetime.datetime.now()

    # Define the directory containing the log files
    log_directory: str = "logs/"

    # Get list of files in the directory
    filelist: List[str] = os.listdir(log_directory)
    # Iterate over files in the logs directory
    for filename in filelist:
        filepath: str = os.path.join(log_directory, filename)
        # Check if the file is a regular file
        if os.path.isfile(filepath):
            try:
                # Get the creation time of the file
                creation_time: datetime.datetime = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
                # Calculate the difference in days
                delta_days: int = (current_date - creation_time).days
                # Check if the file is older than 30 days
                if delta_days > DELETE_FILES_OLDER_THAN_DAYS:
                    # Delete the file
                    os.remove(filepath)
                    logger.info(f"Deleted old log file: {filename}")

            except OSError as e:
                # Log error if the function is unable to get the creation time of a file
                logger.error('Error deleting old log file: %s', e)

    # Log a message indicating the end of the function
    logger.info('........................................................')



# Config Logging


# Config Database as well as the mapping directory
db = config_db()

if db == None:
    logging.error("Error connecting to database")
    exit(1)

logging.info("Database Connected Successfully")

# Set up pinksale scheduler
scheduler = Scheduler(logging, db)

# Schedule the delete log files job to run every 12 hours
schedule.every(DELETE_SERVICE_INTERVAL).hours.do(delete_old_logs)

scheduler.run()

# Schedule the pinksale scrapping job to Run the every 4 hours
schedule.every(SCRAPPING_INTERVAL).minutes.do(scheduler.run)

error_message = f"System Deployed Successfully, Interval: {SCRAPPING_INTERVAL}"
logging.info(error_message)
# Run indefinitely
while True:
    schedule.run_pending()
    time.sleep(1)


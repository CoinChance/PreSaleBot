
import psycopg2
import time
import logging

class Database:
    """
    Database Class

    This class is used to interact with the PostgreSQL database. It handles
    connecting, creating tables, checking if a url is present in the db,
    inserting data into the db and closing the connection.

    Attributes:
        host (str): The hostname of the PostgreSQL database.
        database (str): The name of the database to connect to.
        user (str): The username to authenticate with.
        password (str): The password to authenticate with.
        port (int): The port number to connect to at the host.
        conn (object): The database connection object.
        cur (object): The database cursor object.
        logging (object): The logging object.

    """
    def __init__(self, host, port, database, user, password, logging):
        """
        Initialize the Database object.

        Args:
            host (str): The hostname of the PostgreSQL database.
            database (str): The name of the database to connect to.
            user (str): The username to authenticate with.
            password (str): The password to authenticate with.
            port (int): The port number to connect to at the host.
            logging (object): The logging object.

        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.conn = None
        self.cur = None
        self.logging = logging


    def connect(self):
        """
        Connect to the PostgreSQL database.

        Returns:
            bool: True if connection is established, False otherwise.

        """
        try:
            self.conn = psycopg2.connect(
                user=self.user, 
                password=self.password, 
                host=self.host, 
                port= self.port,
                database=self.database, 
            )
            
            self.cur = self.conn.cursor()
            return True
        except Exception as exp:
            self.logging.error(f"Error connecting to database: {exp}")
            return False


    def close(self):
        """
        Close the database connection.

        """
        if self.conn:
            self.cur.close()
            self.conn.close()


    def create_table(self):
        """
        Create the projects table in the database.

        """
        try:
            # Check if the database exists
            self.cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'presalebot'")
            database_exists = self.cur.fetchone()

            # If the database doesn't exist, create it
            if not database_exists:
                self.cur.execute("CREATE DATABASE presalebot")
                self.logging.info("Database 'presalebot' created successfully.")
            else:
                self.logging.info("Database 'presalebot' already exists.")

            # Create projects table
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    url VARCHAR(255) UNIQUE,
                    name VARCHAR(255), 
                    symbol VARCHAR(255),
                    web VARCHAR(255),
                    twitter VARCHAR(255),
                    telegram VARCHAR(255),
                    token_address VARCHAR(255),
                    supply VARCHAR(255),
                    chain VARCHAR(255),
                    soft_cap VARCHAR(255),
                    start_time VARCHAR,
                    end_time VARCHAR,
                    lockup_time VARCHAR(255),
                    rate VARCHAR(255),
                    raised VARCHAR(255),
                    scrap_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.logging.info("Table 'project_info' created successfully.")

        except psycopg2.Error as e:
            self.logging.error("Error: %s", e)


    

    def check_project_url(self, url):
        """
        Check if the url is present in the database.

        Args:
            url (str): The url to check.

        Returns:
            bool|dict: False if url not present, otherwise a dictionary with
                data if url is present.

        """
        self.cur.execute("SELECT * FROM projects WHERE url = %s", (url,))
        existing_link = self.cur.fetchone()
        if existing_link is None:
            existing_link = False
        return existing_link


    def insert_project_data(self, url, data):
        """
        Insert data into the database.

        Args:
            url (str): The url of the project.
            data (object): The data to insert into the database.

        Returns:
            bool: True if data is inserted successfully, False otherwise.

        """
        try:
            # Begin a transaction
            # self.conn.autocommit = False
            # self.conn.begin()

            # Insert URL into the projects table
            # self.cur.execute("INSERT INTO projects (url) VALUES (%s) RETURNING id", (url,))
            # project_id = self.cur.fetchone()[0]  # Get the generated project ID

            # Insert URL-related data into the project_info table
            self.cur.execute("""
                INSERT INTO projects (
                    url,name, symbol, web, twitter, telegram, token_address, supply,
                    chain, soft_cap, start_time, end_time, lockup_time, rate, raised
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                url, data.name, data.symbol, data.web, data.twitter, data.telegram, data.token_address, data.supply,
                    data.chain, data.soft_cap, data.start_time, data.end_time, data.lockup_time, data.rate, data.raised
            ))

            # Commit the transaction
            self.conn.commit()
            self.logging.info("Data inserted successfully.")
            return True

        except Exception as e:
            # Rollback the transaction in case of an error
            self.conn.rollback()
            self.logging.error("Error while adding record to DB: %s", e)
            return False

        

if __name__ == "__main__":
    db = Database("localhost", "presalebot", "postgres", "presalebot")
    db.connect()
    db.create_table()
    db.close()
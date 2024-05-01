FROM python:3.12

ARG DEBIAN_FRONTEND=noninteractive

# Install Firefox
RUN apt-get update && apt-get install -y firefox-esr

# Set display port to avoid crash
ENV DISPLAY=:99

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir psycopg2-binary selenium webdriver_manager schedule python-dotenv


# Set the working directory in the container
WORKDIR /app

# Copy the Python code into the container
COPY . .

# Copy the init.sql file to the Docker image
COPY ./db/init.sql /docker-entrypoint-initdb.d/

# Run the Python script
CMD ["python", "app.py"]



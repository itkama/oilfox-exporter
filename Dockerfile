# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add the script file that queries the API and serves the /metrics endpoint
ADD main.py /app

# Needed for displaying the metrics
RUN pip install --trusted-host pypi.python.org prometheus_client

# Make port 8000 available to access the /metrics endpoint
# EXPOSE 8000

# Enviroment variables to authenticate against the oilfox-api
# ENV EMAIL=default_email
# ENV PASSWORD=default_password

# Run main.py when the container launches
CMD ["python", "main.py", "--email", "$EMAIL", "--password", "$PASSWORD"]
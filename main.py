import argparse
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from prometheus_client import start_http_server, Gauge, generate_latest, CollectorRegistry
from datetime import datetime, timedelta

# Argument parsing
parser = argparse.ArgumentParser(description='Prometheus Exporter for Oilfox API. See https://github.com/foxinsights/customer-api/tree/main/docs/v1 for more information about the API.')
parser.add_argument('--email', type=str, required=True, help='Email for API authentication')
parser.add_argument('--password', type=str, required=True, help='Password for API authentication')
args = parser.parse_args()
email = args.email
password = args.password

# Create a custom registry
registry = CollectorRegistry()

# Define custom metrics for each hwid
fill_level_percent = Gauge('oilfox_fill_level_percent', 'Fill Level Percentage of Tank', ['hwid'], registry=registry)
fill_level_quantity = Gauge('oilfox_fill_level_quantity', 'Fill Level Quantity of Tank in litres', ['hwid'], registry=registry)
validation_error = Gauge('oilfox_validation_error', 'Validation Error', ['hwid'], registry=registry)

# Initialize last API query time to a very old time (to ensure the first query happens)
last_api_query_time = datetime.min
# Initialize a variable to store the last API response
last_api_response = {}

# Error code mapping
error_mapping = {
    'NO_ERROR': 0,
    'NO_METERING': 1,
    'EMPTY_METERING': 2,
    'NO_EXTRACTED_VALUE': 3,
    'SENSOR_CONFIG': 4,
    'MISSING_STORAGE_CONFIG': 5,
    'INVALID_STORAGE_CONFIG': 6,
    'DISTANCE_TOO_SHORT': 7,
    'ABOVE_STORAGE_MAX': 8,
    'BELOW_STORAGE_MIN': 9
}

def queryOilfoxAPI():
    url_login = "https://api.oilfox.io/customer-api/v1/login"
    url_device = "https://api.oilfox.io/customer-api/v1/device"

    headers_login = {'Content-Type': 'application/json'}
    data_login = {"password": password, "email": email}

    # First API call to get the access token
    auth_response = requests.post(url_login, headers=headers_login, json=data_login)
    access_token = ""

    if auth_response.status_code == 200:
        # Assuming the response is in JSON format
        response_data = auth_response.json()

        # Extract the access token
        access_token = response_data.get("access_token")

        # Second API call using the access token
        headers_device = {'Authorization': f'Bearer {access_token}'}
        device_response = requests.get(url_device, headers=headers_device)

        if device_response.status_code == 200:
            # Assuming the response is in JSON format
            return device_response.json()
        else:
            print(f"Device API Error: {device_response.status_code}, {device_response.text}")
    else:
        print(f"Login API Error: {auth_response.status_code}, {auth_response.text}")

def limitAPIcalls():
    global last_api_query_time, last_api_response
    current_time = datetime.now()
    if (current_time - last_api_query_time).total_seconds() >= 2 * 60 * 60:
        last_api_response = queryOilfoxAPI()
        last_api_query_time = current_time
    return last_api_response

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(generate_latest(registry))
            
            api_data = limitAPIcalls()
            # Update metrics based on API data
            for item in api_data.get('items', []):
                hwid = item['hwid']

                # Get fill level percent and quantity, default to -1 if not present
                fill_percent = item.get('fillLevelPercent', -1)
                fill_quantity = item.get('fillLevelQuantity', -1)

                # Get validation error, default to 'NO_ERROR' if not present
                error_value = item.get('validationError', 'NO_ERROR')
                error_code = error_mapping.get(error_value, -1)  # default to -1 if the error string is not in mapping

                # Update Prometheus metrics
                fill_level_percent.labels(hwid).set(fill_percent)
                fill_level_quantity.labels(hwid).set(fill_quantity)
                validation_error.labels(hwid).set(error_code)
        else:
            self.send_response(404)
            self.end_headers()
            #self.wfile.write(b'Hello, this is a custom exporter!\n')

# Start the HTTP server and expose metrics on :8080/metrics
start_http_server(8080)

# Pre-populate metrics upon startup
initial_api_data = queryOilfoxAPI()
for item in initial_api_data.get('items', []):
    hwid = item['hwid']
    fill_percent = item.get('fillLevelPercent', -1)
    fill_quantity = item.get('fillLevelQuantity', -1)
    error_value = item.get('validationError', 'NO_ERROR')
    error_code = error_mapping.get(error_value, -1)  # default to -1 if the error string is not in mapping

    fill_level_percent.labels(hwid).set(fill_percent)
    fill_level_quantity.labels(hwid).set(fill_quantity)
    validation_error.labels(hwid).set(error_code)

# Start the custom HTTP server
httpd = HTTPServer(('0.0.0.0', 8000), RequestHandler)
print('Exporter is running on :8000')
httpd.serve_forever()

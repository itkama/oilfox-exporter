# oilfox-exporter
A small little Prometheus exporter for the [FoxInsight.ai Customer API](https://github.com/foxinsights/customer-api).

Exposes the fill_level_percent and fill_level_quantity values of each hwid associated with the customer account used.
Also exposes a metric should a validationError be returned by the API.

# Error code mapping
error_mapping = {
    'SOMETHING_WENT_REALLY_WRONG': -1,
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

If any metric returns -1, that means something went really wrong, possibly missing an API response or an unknown error.


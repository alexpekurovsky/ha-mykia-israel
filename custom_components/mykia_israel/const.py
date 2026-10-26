"""Constants for the Kia Ituran integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "mykia_israel"

CONF_PHONE_NUMBER: Final = "phone_number"
CONF_PLATE_NUMBER: Final = "plate_number"
CONF_DEVICE_ID: Final = "device_id"
CONF_USERNAME: Final = "username"
CONF_OTP: Final = "otp"

UPDATE_INTERVAL = timedelta(seconds=300)

# API
BASE_URL = "https://app.ituran.com/ituranmobileservice/mobileservice.asmx/"
APP_ID = "69"
USER_AGENT = "MY KIA/1.0.53 (ANDROID)"
IMS_NAMESPACE = "http://www.ituran.com/IturanMobileService"

# ECM status codes from GetActiveStatusesbyUserPlatform
ECM_ENGINE_OFF = "31"
ECM_LOCKED = "41"

# EV DiagnosticValues label fragments (partial match)
EV_CHARGING_MODE_LABELS: list[str] = [
    "Charging AC Mode",
    "Charging DC Mode",
    "Charging Mode Status",
]
EV_BATTERY_LEVEL_LABELS: list[str] = ["Battery Status Of Charge"]
EV_BATTERY_RANGE_LABELS: list[str] = ["Vehicle Range Of Battery"]
EV_CHARGING_TIME_LABELS: list[str] = [
    "Time Remaining",
    "Remaining For Charge",
    "Remaining Charge",
]

# API error strings
ERROR_OK = "ok"
ERROR_INVALID_CREDENTIALS = "IncorrectUserNameOrPassword"

"""API client for Kia Ituran Israel service."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import logging

import aiohttp

from .const import (
    APP_ID,
    BASE_URL,
    ERROR_INVALID_CREDENTIALS,
    ERROR_OK,
    IMS_NAMESPACE,
    USER_AGENT,
)
from .exceptions import KiaIturanApiError, KiaIturanAuthError
from .vehicle import KiaVehicle

_LOGGER = logging.getLogger(__name__)

_NS = f"{{{IMS_NAMESPACE}}}"


def _strip_ns(xml_text: str) -> str:
    """Strip default namespace declarations so bare tag names work."""
    return re.sub(r'\s+xmlns(?::[^=]+)?="[^"]*"', "", xml_text)


def _find_text(root: ET.Element, tag: str) -> str:
    """Find a tag at any depth, return its text or empty string."""
    el = root.find(".//" + tag)
    return el.text.strip() if el is not None and el.text else ""


class KiaIturan:
    """Client for the Kia/Ituran Israel API.

    Auth flow:
      1. request_otp()  — registers device_id with server, sends OTP SMS
      2. authenticate() — confirms OTP, retrieves username
    After that, all data calls use username + device_id as credentials.
    device_id is permanent and never expires.
    """

    def __init__(
        self,
        phone_number: str,
        plate_number: str,
        device_id: str,
        username: str | None = None,
    ) -> None:
        self._phone = phone_number
        self._plate = plate_number
        self._device_id = device_id
        self._username = username

    # ------------------------------------------------------------------ #
    # Properties persisted in the config entry                            #
    # ------------------------------------------------------------------ #

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def username(self) -> str | None:
        return self._username

    # ------------------------------------------------------------------ #
    # Auth                                                                #
    # ------------------------------------------------------------------ #

    async def is_authenticated(self) -> bool:
        """Return True if current credentials work."""
        if not self._username:
            return False
        try:
            await self.get_vehicles()
            return True
        except KiaIturanAuthError:
            return False

    async def request_otp(self) -> None:
        """Trigger OTP SMS via ImporterActivationWithAppId.

        Registers device_id with the server. The same device_id must be used
        for all subsequent data calls as the password.
        """
        data = aiohttp.FormData()
        data.add_field("PhoneNumber", self._phone)
        data.add_field("Plate", self._plate)
        data.add_field("Key", self._device_id)
        data.add_field("AppId", APP_ID)
        try:
            xml_text = await self._post("ImporterActivationWithAppId", data)
            root = ET.fromstring(_strip_ns(xml_text))
            error = _find_text(root, "ReturnError")
            if error.lower() not in ("", ERROR_OK, "nothing"):
                raise KiaIturanAuthError(error)
        except KiaIturanAuthError:
            raise
        except Exception as exc:
            _LOGGER.error("request_otp failed: %s", exc)
            raise KiaIturanApiError(exc) from exc

    async def authenticate(self, otp: str) -> None:
        """Confirm OTP and retrieve username via ImporterSerializationRequestAll.

        After this call, use username + device_id for all data calls.
        """
        data = aiohttp.FormData()
        data.add_field("OTPcode", otp)
        data.add_field("Plate", self._plate)
        data.add_field("PhoneNumber", self._phone)
        data.add_field("AppId", APP_ID)
        try:
            xml_text = await self._post("ImporterSerializationRequestAll", data)
            root = ET.fromstring(_strip_ns(xml_text))
            error = _find_text(root, "ReturnError")
            # "Nothing" = primary driver, "UserNotFound" = secondary — both OK
            if error.lower() not in ("", ERROR_OK, "nothing", "usernotfound"):
                raise KiaIturanAuthError(error)
            self._username = _find_text(root, "UserName")
            _LOGGER.debug("Authenticated: username=%s", self._username)
        except KiaIturanAuthError:
            raise
        except Exception as exc:
            _LOGGER.error("authenticate failed: %s", exc)
            raise KiaIturanApiError(exc) from exc

    # ------------------------------------------------------------------ #
    # Data                                                                #
    # ------------------------------------------------------------------ #

    async def get_vehicles(self) -> list[KiaVehicle]:
        """Fetch all vehicles with location and status data."""
        if not self._username:
            raise KiaIturanAuthError("Not authenticated")

        try:
            # --- GetUserPlatforms ---
            data = aiohttp.FormData()
            data.add_field("UserName", self._username)
            data.add_field("Password", self._device_id)
            data.add_field("GetAddress", "true")
            xml_text = await self._post("GetUserPlatforms", data)
            root = ET.fromstring(xml_text)

            return_code = (root.findtext(f"{_NS}ReturnCode") or "").upper()
            if return_code != "OK":
                error_desc = root.findtext(f"{_NS}ErrorDescription") or return_code
                if ERROR_INVALID_CREDENTIALS in error_desc:
                    raise KiaIturanAuthError(error_desc)
                raise KiaIturanApiError(error_desc)

            veh_list = root.find(f"{_NS}VehList")
            if veh_list is None:
                return []

            vehicles: list[KiaVehicle] = []
            for veh in veh_list:
                platform_id = veh.findtext(f"{_NS}PlatformId") or ""
                ecm_codes = await self._get_ecm_codes(platform_id)
                electric_data = await self._get_electric_data(platform_id)
                vehicles.append(KiaVehicle(veh, ecm_codes, electric_data))

            return vehicles

        except (KiaIturanAuthError, KiaIturanApiError):
            raise
        except Exception as exc:
            _LOGGER.error("get_vehicles failed: %s", exc)
            raise KiaIturanApiError(exc) from exc

    async def _get_ecm_codes(self, platform_id: str) -> set[str]:
        """Fetch active ECM status codes for a vehicle."""
        data = aiohttp.FormData()
        data.add_field("UserName", self._username)
        data.add_field("Password", self._device_id)
        data.add_field("PlatformId", platform_id)
        try:
            xml_text = await self._post("GetActiveStatusesbyUserPlatform", data)
            root = ET.fromstring(xml_text)
            return {el.text for el in root.iter(f"{_NS}EcmCode") if el.text}
        except Exception as exc:
            _LOGGER.warning("_get_ecm_codes failed for %s: %s", platform_id, exc)
            return set()

    async def _get_electric_data(self, platform_id: str) -> ET.Element | None:
        """Fetch EV DiagnosticValues for a vehicle. Returns None for non-EV or on error."""
        data = aiohttp.FormData()
        data.add_field("UserName", self._username)
        data.add_field("Password", self._device_id)
        data.add_field("PlatformId", platform_id)
        try:
            xml_text = await self._post("GetElectricData", data)
            root = ET.fromstring(xml_text)
            return_code = (root.findtext(f"{_NS}ReturnCode") or "").upper()
            if return_code != "OK":
                return None
            return root.find(f".//{_NS}DiagnosticValues")
        except Exception as exc:
            _LOGGER.warning("_get_electric_data failed for %s: %s", platform_id, exc)
            return None

    # ------------------------------------------------------------------ #
    # HTTP                                                                #
    # ------------------------------------------------------------------ #

    async def _post(self, endpoint: str, data: aiohttp.FormData) -> str:
        async with aiohttp.ClientSession(
            headers={"User-Agent": USER_AGENT}
        ) as session:
            async with session.post(BASE_URL + endpoint, data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    raise KiaIturanApiError(f"HTTP {resp.status} from {endpoint}")
                return await resp.text()

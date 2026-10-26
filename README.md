# My Kia Israel — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for **Kia vehicles with Ituran GPS tracking in Israel** (MY KIA app / Talcar).

Mirrors the built-in [Ituran integration](https://www.home-assistant.io/integrations/ituran/) but uses the Kia Importer authentication flow (phone number + license plate + OTP) instead of ID/passport.

> **Disclaimer:** This is an unofficial community project. It is not affiliated with, endorsed by, or supported by Kia, Talcar, or Ituran. It relies on undocumented private APIs that may change or break at any time without notice.

Inspired by [ha-kia-Ituran](https://github.com/tomerezra/ha-kia-Ituran) and the official [Ituran integration](https://www.home-assistant.io/integrations/ituran/).

## Features

- **Device tracker** — real-time GPS location on the HA map
- **Sensors**: speed, mileage, battery voltage, address, heading, last update from vehicle
- **Binary sensors**: engine on/off, locked/unlocked
- **EV sensors** (electric vehicles only): battery level, range, charging mode, charging time remaining, and all other diagnostic values returned by the API
- Automatic polling every 5 minutes
- Re-authentication support if credentials expire

## Requirements

- Kia vehicle registered with Ituran/Talcar Israel (MY KIA app)
- Israeli mobile phone number associated with the vehicle
- Home Assistant 2024.1.0 or newer

## Installation

### Via HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alexpekurovsky&repository=ha-mykia-israel&category=integration)

Or manually:

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/alexpekurovsky/ha-mykia-israel` as **Integration**
3. Search for "My Kia Israel" and install
4. Restart Home Assistant

### Manual

1. Copy `custom_components/mykia_israel/` to your HA `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **My Kia Israel**
3. Enter your mobile phone number and vehicle license plate
4. Enter the OTP code sent to your phone
5. Done — your vehicle will appear as a device with all entities

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `device_tracker.<plate>_car` | Device tracker | GPS location |
| `sensor.<plate>_speed` | Sensor | Current speed (km/h) |
| `sensor.<plate>_mileage` | Sensor | Total mileage (km) |
| `sensor.<plate>_battery_voltage` | Sensor | 12V battery voltage (V) |
| `sensor.<plate>_address` | Sensor | Current street address |
| `sensor.<plate>_heading` | Sensor | Compass heading (°) |
| `sensor.<plate>_last_update_from_vehicle` | Sensor | Timestamp of last GPS update |
| `binary_sensor.<plate>_engine` | Binary sensor | Engine running state |
| `binary_sensor.<plate>_locked` | Binary sensor | Lock state |
| `sensor.<plate>_battery_level` | Sensor | EV battery charge (%) |
| `sensor.<plate>_battery_range` | Sensor | EV remaining range (km) |
| `sensor.<plate>_charging_mode` | Sensor | EV charging mode (AC/DC/Off) |
| `sensor.<plate>_charging_time_remaining` | Sensor | EV time remaining to full charge |
| `binary_sensor.<plate>_charging` | Binary sensor | EV charging state |

EV entities are only created for electric vehicles. Additional diagnostic sensors are created automatically for any extra data values returned by the API.

## Notes

- The integration communicates with `app.ituran.com` (Ituran Israel / Talcar)
- Data is polled every 5 minutes (same as the MY KIA app)
- Only vehicles registered under the My Kia / Talcar program in Israel are supported

## License

MIT

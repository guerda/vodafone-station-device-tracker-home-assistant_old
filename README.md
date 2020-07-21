# Home Assistant Device Tracker for Vodafone Power Station

This is a Home Assistant Device Tracker that works with the italian version of Vodafone Power Station.

It extracts the list of connected devices and expose them to Home Assistant.

## Installation

### Option 1

Use [HACS](https://hacs.xyz/) and add this repo: `https://github.com/paoloantinori/ha_vodafone_power_station_device_tracker`.

### Option 2

Manually copy the content of this repo in your `custom_components/` folder.


## Configuration

Add this tracker to your `device_tracker` section:

```yaml
- platform: vodafone_power_station
  interval_seconds: 60
  host: XX.XX.XX.XX
  username: your_username_here
  password: 'your_password_here'
  new_device_defaults:
    track_new_devices: False
```

To enable logging:

```yaml
logger:
  default: info
  logs:
    custom_components.vodafone_power_station.device_tracker: info
```

The discovered devices will be listed in the `known_devices.yaml` file.


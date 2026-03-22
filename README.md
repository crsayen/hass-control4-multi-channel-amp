# Control4 Multi-Channel Amplifier

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs)
[![GitHub Release](https://img.shields.io/github/v/release/crsayen/hass-control4-multi-channel-amp?style=for-the-badge)](https://github.com/crsayen/hass-control4-multi-channel-amp/releases)
[![GitHub Stars](https://img.shields.io/github/stars/crsayen/hass-control4-multi-channel-amp?style=for-the-badge)](https://github.com/crsayen/hass-control4-multi-channel-amp/stargazers)

A [Home Assistant](https://www.home-assistant.io/) custom integration for controlling Control4 multi-channel amplifiers over UDP.

Each configured zone gets a media player, power switch, volume slider, and source selector — all kept in sync through shared state.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=crsayen&repository=hass-control4-multi-channel-amp&category=integration)

Or manually:

1. Open HACS > Integrations > three-dot menu > **Custom repositories**
2. Add `crsayen/hass-control4-multi-channel-amp` with category **Integration**
3. Install **Control4 Multi-Channel Amplifier**
4. Restart Home Assistant

### Manual

Copy `custom_components/c4_amp/` into your Home Assistant `custom_components/` directory and restart.

## Configuration

Add zones to your `configuration.yaml`:

```yaml
c4_amp:
  Living Room:
    ip: 192.168.0.145
    channel: 1
    sources:
      2: WiiM
      1: EA5
  Kitchen:
    ip: 192.168.0.145
    channel: 2
    sources:
      2: WiiM
      1: EA5
```

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `ip` | Yes | | IP address of the amplifier |
| `channel` | Yes | | Output channel (1–8) |
| `port` | No | `8750` | UDP port |
| `sources` | No | `{}` | Map of input ID to friendly name |

## Entities

Each zone creates the following entities:

| Entity | Domain | Description |
|--------|--------|-------------|
| `{zone}` | `media_player` | Media player with on/off and source selection |
| `{zone} Power` | `switch` | Power on/off |
| `{zone} Volume` | `number` | Volume level (0.00–1.00) |
| `{zone} Source` | `select` | Source selector (only if `sources` is configured) |

All entities for a zone share state — toggling power from the switch is immediately reflected in the media player and vice versa.

## How it works

The integration communicates with the amplifier using UDP commands. Each command is sent with a 50ms response timeout and up to 3 retries to handle dropped packets. Commands to the same channel are serialized — if a new command arrives while a previous one is still retrying, the old command is cancelled so the most recent action always wins.

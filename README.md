# Control4 Multi-Channel Amplifier

A Home Assistant custom integration for controlling multi-zone audio amplifiers from Control4. Communicates with the amp over UDP (default port 8750).

## Installation

### HACS (recommended)

1. Add this repository to HACS as a custom repository (type: Integration)
2. Install "Control4 Multi-Channel Amplifier" from HACS
3. Restart Home Assistant
4. Add configuration to `configuration.yaml`

### Manual

Copy `custom_components/c4_amp/` into your Home Assistant `custom_components` folder, restart, then add configuration to `configuration.yaml`.

## Configuration

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

| Key | Required | Description |
|-----|----------|-------------|
| `ip` | Yes | IP address of the amp |
| `channel` | Yes | Output channel number (1–8) |
| `port` | No | UDP port (default: `8750`) |
| `sources` | No | Map of input ID → friendly name |

## Entities

For each configured zone the integration creates:

| Entity | Domain | Description |
|--------|--------|-------------|
| `{zone}` | `media_player` | Full media player with on/off and source selection |
| `{zone} Power` | `switch` | Binary power control |
| `{zone} Volume` | `number` | Volume slider (0.0–1.0) |
| `{zone} Source` | `select` | Source selector (only created if sources are configured) |

All entities share the same underlying state, so changes from any entity are immediately reflected in the others.

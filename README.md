# EcoWorthy BMS Gateway

A read-only gateway for ECO-WORTHY BW02 and JBD/DP04 BLE battery-management systems. The LXC owns Bluetooth acquisition and exposes a versioned LAN API. Home Assistant never accesses Bluetooth.

## Architecture

```text
EcoWorthy/JBD batteries -- BLE --> collector in LXC --> atomic state.json
                                                       |
                                                       +--> read-only HTTP API :8765
                                                                |
                                                                +--> Home Assistant custom integration
```

The collector uses pinned `aiobmsble==0.27.0`, preserves every native metric, and derives stable normalized fields. Failed BLE polls retain the last known values but mark each battery unavailable/stale; old measurements are never changed to zero.

## LAN API

```bash
curl "http://${GATEWAY_HOST}:8765/healthz"
curl "http://${GATEWAY_HOST}:8765/api/v1/status"
```

The API serves only the collector's atomic JSON state. It cannot trigger scans, BLE connections, writes, or BMS commands. `/api/v1/status` is versioned and derives freshness at request time. LAN HTTP is the default for simplicity; do not expose port `8765` to the Internet. Optional bearer-token support is available through `eco-bms-api --token-file /path/to/root-owned-token` without embedding a secret in source.

## Home Assistant installation through the GUI

This repository is HACS-compatible, so no terminal, SSH, YAML, or manual file copying is required.

1. Open **HACS** in Home Assistant.
2. Select the three-dot menu in the upper-right, then **Custom repositories**.
3. Add `https://github.com/Jefferderp/ecoworthy-bms-ha` with type **Integration**.
4. Open **EcoWorthy BMS Gateway** in HACS and select **Download**.
5. Restart Home Assistant when HACS prompts you.
6. Open **Settings → Devices & services → Add integration**.
7. Search for **EcoWorthy BMS Gateway**.
8. Enter the LAN hostname or IP address of your gateway and select **Submit**.

Typical configuration:

```text
Host: LAN hostname or IP address of the gateway
Port: 8765
Use HTTPS: off
Bearer token: blank unless authentication is enabled on the gateway
Update interval: 30 seconds
```

The integration validates the live gateway before saving. The host is deliberately not hardcoded, and the optional bearer token is entered using a password field. Reconfigure the host, port, TLS, token, or polling interval from the integration entry.

### Entities

Each physical battery is a Home Assistant device identified by its stable Bluetooth MAC. Available native data determines which entities are created:

- State of charge, voltage, signed current, power, temperature, remaining capacity
- Charge/discharge direction, state of health, cycle count
- ETA to empty/full when the BMS and current permit calculation
- Minimum/maximum/delta cell voltage and every individual cell voltage
- Every reported temperature probe
- Signal strength, sample age, connectivity, charging, problem state
- Charge/discharge MOSFET diagnostic entities when reported

Correct Home Assistant device classes, units, state classes, entity categories, translations, unique IDs, diagnostics redaction, coordinator polling, config flow, reconfigure flow, and reauthentication flow are included.

## Collector CLI

```bash
eco-bms --help
eco-bms scan --timeout 20
eco-bms poll
eco-bms watch --interval 5
eco-bms daemon --interval 30
```

Global options precede the command. Repeat `--battery 'MAC=name:driver'` to override defaults.

## Service operations

```bash
systemctl status ecoworthy-bms ecoworthy-bms-api
journalctl -u ecoworthy-bms -u ecoworthy-bms-api -f
curl -fsS http://127.0.0.1:8765/healthz
systemctl restart ecoworthy-bms-api
```

Persistent state: `/var/lib/ecoworthy-bms/state.json`  
API identity: `/etc/ecoworthy-bms/server-id`  
API endpoint: `http://GATEWAY_HOST:8765/api/v1/status`

An LXC can consume a filtered host BlueZ D-Bus socket because Linux Bluetooth HCI sockets cannot operate outside the initial network namespace. BLE access can use host BlueZ through a filtered `org.bluez` proxy.

**Not safety-critical:** reverse-engineered telemetry and LAN availability must not control battery protection, thermal protection, charging cutoffs, or other safety systems.

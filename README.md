# Cisco Switch Administration with Python

This template uses [Netmiko](https://github.com/ktbyers/netmiko) to connect to a
Cisco IOS switch over SSH. The example target is `172.20.0.18`, but the host
can be changed with an environment variable or a command-line option.

The URL `https://172.20.0.18/` is an HTTPS web address. For this script, use
the switch IP as the host and connect through SSH, normally on port `22`.

## Setup

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `SWITCH_USERNAME`. You can leave `SWITCH_PASSWORD` blank;
the script will securely prompt for it. Do not commit `.env`.

## Read-only commands

The default command set collects version, interface summary, and interface
status information:

```bash
python cisco_switch.py
```

Run specific show commands:

```bash
python cisco_switch.py --show "show running-config" "show vlan brief"
```

## Configuration commands

Configuration mode is explicit and saves the running configuration after the
commands complete:

```bash
python cisco_switch.py --configure \
  "interface GigabitEthernet1/0/1" \
  "description Managed by Python" \
  "switchport mode access"
```

Only use `--configure` when you have confirmed the target switch and commands.
Test changes in a lab first, and ensure your account has the required Cisco
privileges.

## Command-line overrides

Environment values can be overridden for one invocation:

```bash
python cisco_switch.py \
  --host 172.20.0.18 \
  --port 22 \
  --username admin \
  --show "show clock"
```

The script supports other Netmiko device types by setting
`SWITCH_DEVICE_TYPE` or passing `--device-type`, such as `cisco_xe`.

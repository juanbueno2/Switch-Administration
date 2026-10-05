#!/usr/bin/env python3
"""Basic SSH administration template for Cisco IOS switches."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from collections.abc import Sequence

from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)


DEFAULT_SHOW_COMMANDS = (
    "show version",
    "show ip interface brief",
    "show interfaces status",
    "do show vlan brief",
)


def build_connection_options(args: argparse.Namespace) -> dict[str, object]:
    """Build Netmiko connection options without storing secrets in source code."""
    host = args.host or os.getenv("SWITCH_HOST")
    username = args.username or os.getenv("SWITCH_USERNAME")
    password = args.password or os.getenv("SWITCH_PASSWORD")
    device_type = args.device_type or os.getenv("SWITCH_DEVICE_TYPE", "cisco_ios")
    port = args.port or int(os.getenv("SWITCH_PORT", "22"))

    if not host:
        raise ValueError("A switch host is required (--host or SWITCH_HOST).")
    if not username:
        raise ValueError(
            "A username is required (--username or SWITCH_USERNAME)."
        )
    if not password:
        password = getpass.getpass(f"SSH password for {username}@{host}: ")

    return {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
        "port": port,
        "fast_cli": False,
    }


def show_commands(connection_options: dict[str, object], commands: Sequence[str]) -> None:
    """Connect to the switch and print the output of read-only commands."""
    with ConnectHandler(**connection_options) as connection:
        print(f"Connected to {connection_options['host']}")
        for command in commands:
            print(f"\n$ {command}")
            print(connection.send_command(command))


def configure_switch(
    connection_options: dict[str, object], commands: Sequence[str]
) -> None:
    """Apply configuration commands and save the running configuration."""
    if not commands:
        raise ValueError("At least one configuration command is required.")

    with ConnectHandler(**connection_options) as connection:
        print(f"Connected to {connection_options['host']}")
        output = connection.send_config_set(list(commands))
        print(output)
        print("\nSaving running configuration...")
        print(connection.save_config())


def set_port_description(
    connection_options: dict[str, object], interface: str, description: str
) -> None:
    """Set and save a description on one switch interface."""
    configure_switch(
        connection_options,
        [f"interface {interface}", f"description {description}"],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run read-only or configuration commands on a Cisco IOS switch."
    )
    parser.add_argument("--host", help="Switch IP address or hostname.")
    parser.add_argument("--port", type=int, help="SSH port (default: 22).")
    parser.add_argument("--username", help="SSH username.")
    parser.add_argument(
        "--password",
        help="SSH password. Prefer SWITCH_PASSWORD or the interactive prompt.",
    )
    parser.add_argument(
        "--device-type",
        help="Netmiko device type (default: cisco_ios).",
    )
    parser.add_argument(
        "--show",
        nargs="+",
        metavar="COMMAND",
        help="Run one or more read-only show commands.",
    )
    parser.add_argument(
        "--configure",
        nargs="+",
        metavar="COMMAND",
        help="Apply configuration commands and save the configuration.",
    )
    parser.add_argument(
        "--set-port-description",
        nargs=2,
        metavar=("INTERFACE", "DESCRIPTION"),
        help="Set an interface description and save the configuration.",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    selected_actions = sum(
        action is not None for action in (args.show, args.configure, args.set_port_description)
    )
    if selected_actions > 1:
        print(
            "Choose only one of --show, --configure, or --set-port-description.",
            file=sys.stderr,
        )
        return 2

    try:
        connection_options = build_connection_options(args)
        if args.set_port_description:
            interface, description = args.set_port_description
            set_port_description(connection_options, interface, description)
        elif args.configure:
            configure_switch(connection_options, args.configure)
        else:
            show_commands(connection_options, args.show or DEFAULT_SHOW_COMMANDS)
    except (NetmikoAuthenticationException, NetmikoTimeoutException) as error:
        print(f"SSH connection failed: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

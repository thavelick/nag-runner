#!/usr/bin/python3
"Nag Runner: Reminds you to run important commands on a regular basis."

import argparse
import json
import os
import sys
from collections import namedtuple
from datetime import datetime, timedelta
from subprocess import call


Entry = namedtuple("Entry", ["name", "command", "interval"])


class NagRunnerException(Exception):
    "Base exception for nag_runner."


class InvalidConfigException(NagRunnerException):
    "Raised when the config is invalid."


class InvalidEntryException(NagRunnerException):
    "Raised when the entry is invalid."


class MissingConfigException(NagRunnerException):
    "Raised when the config is missing."


class NagRunner:
    "main class for nag runner."

    def __init__(self, config_path, last_run_path=None):
        self.config = self.load_config(config_path)
        self.last_run_path = last_run_path or os.path.expanduser(
            "~/.cache/nag_runner/last_run.json"
        )

    def load_config(self, config_file):
        "Loads a list of Entries from the config file."
        possible_config_files = (
            [config_file]
            if config_file
            else [
                os.path.expanduser(path)
                for path in ["~/.config/nag_runner.json", "~/.nag_runner.json"]
            ]
        )
        for possible_config_file in possible_config_files:
            if os.path.exists(possible_config_file):
                with open(possible_config_file, "r", encoding="utf-8") as file:
                    config_data = json.load(file)
                    return [Entry(**entry_data) for entry_data in config_data]

        raise MissingConfigException(
            f"No config file found at {', '.join(possible_config_files)}"
        )

    def get_last_run(self, name):
        "Returns the last run time for a command."
        if not os.path.exists(self.last_run_path):
            return None

        with open(self.last_run_path, "r", encoding="utf-8") as file:
            last_run = json.load(file)

        if name not in last_run:
            return None

        return datetime.strptime(last_run[name], "%Y-%m-%dT%H:%M:%S.%f")

    def get_entry_by_name(self, name):
        "Returns the entry with the given name."
        for entry in self.config:
            if entry.name == name:
                return entry
        raise InvalidEntryException(f"Could not find entry with name {name}")

    def list_entries_next_run(self):
        "Lists all entries and when they will next run."
        for entry in self.config:
            last_run = self.get_last_run(entry.name)
            if last_run:
                next_run = last_run + timedelta(days=int(entry.interval))
                days_until_next_run = (next_run - datetime.now()).days
            else:
                days_until_next_run = 0

            print(f"{entry.name}: Next run in {days_until_next_run} days")

    def run_entry(self, entry):
        "Runs the command and set it's last run date."
        call(entry.command, shell=True)
        self.set_last_run(entry)

    def run_entry_by_name(self, name):
        "Runs the entry with the given name."
        entry = self.get_entry_by_name(name)
        self.run_entry(entry)

    def set_last_run(self, entry):
        "Don't run the command this time and reset the interval."
        last_run = {}
        if os.path.exists(self.last_run_path):
            with open(self.last_run_path, "r", encoding="utf-8") as file:
                last_run = json.load(file)
        else:
            os.makedirs(os.path.dirname(self.last_run_path), exist_ok=True)
        last_run[entry.name] = datetime.now().isoformat()
        with open(self.last_run_path, "w", encoding="utf-8") as file:
            json.dump(last_run, file)

    def print_next_time_message(self, _entry):
        "Do not run the command, but still nag me next time."
        print("Ok, I'll nag you next time")

    def print_menu(self, _entry):
        "Show the help menu"
        print("Possible responses are:")
        for responses, method in self.get_user_actions():
            print(f"{responses[0]}: {method.__doc__}")

    def get_user_actions(self):
        "Returns a list of actions the user can take."
        return [
            # (responses, method, ask_again)
            (["y", "Y", ""], self.run_entry, False),
            (["n", "N"], self.print_next_time_message, False),
            (["d"], self.set_last_run, False),
            (["?"], self.print_menu, True),
        ]

    def run_overdue_entries(self):
        "Runs all overdue entries."
        for entry in self.config:
            last_run = self.get_last_run(entry.name)
            if last_run:
                delta = datetime.now() - last_run
                if delta < timedelta(days=int(entry.interval)):
                    continue

                prompt = (
                    f"It has been {delta.days} days since you last ran {entry.name}. "
                    "Run now? [Y/n/d/?] "
                )
            else:
                prompt = f"You have never run {entry.name}. Run now? [Y/n/d/?] "

            keep_going = True
            while keep_going:
                print(prompt, end="")
                response = input()
                for responses, method, ask_again in self.get_user_actions():
                    if response in responses:
                        method(entry)
                        keep_going = ask_again


def main():
    "Main function."
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-path", "-c", help="Path to the config file")
    parser.add_argument("--last-run-path", "-l", help="Path to the last run file")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--name", "-n", help="Name of a single entry to run")
    group.add_argument(
        "--list",
        action="store_true",
        help="List all entries and when they will next run",
    )
    args = parser.parse_args()

    nag_runner = NagRunner(args.config_path, args.last_run_path)

    if args.name:
        nag_runner.run_entry_by_name(args.name)
    elif args.list:
        nag_runner.list_entries_next_run()
    else:
        nag_runner.run_overdue_entries()


if __name__ == "__main__":
    try:
        main()
    except NagRunnerException as e:
        print(e)
        sys.exit(1)

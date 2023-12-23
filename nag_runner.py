#!/usr/bin/python3
import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from subprocess import call


@dataclass
class Entry:
    name: str
    command: str
    interval: int

    @classmethod
    def from_dict(cls, entry_dict):
        "convert from a dict."

        for key in ["name", "command", "interval"]:
            if key not in entry_dict:
                raise InvalidConfigException(f"No {key} specified")
        return cls(**entry_dict)


class NagRunnerException(Exception):
    "Base exception for nag_runner."


class InvalidConfigException(NagRunnerException):
    "Raised when the config is invalid."


class InvalidEntryException(NagRunnerException):
    "Raised when the entry is invalid."


class MissingConfigException(NagRunnerException):
    "Raised when the config is missing."


class NagRunner:
    def __init__(self, config_path, last_run_path=None):
        self.config = self.load_config(config_path)
        self.last_run_path = last_run_path or self.get_default_last_run_path()

    def load_config(self, config_file=None):
        "Loads a list of Entries from the config file."
        config_file = config_file or self.find_config_path()
        with open(config_file, "r", encoding="utf-8") as file:
            return [Entry.from_dict(entry) for entry in json.load(file)]

    def find_config_path(self):
        "Returns the path to the config file."
        possible_config_files = [
            os.path.join(os.path.expanduser("~"), ".config", "nag_runner.json"),
            os.path.join(os.path.expanduser("~"), ".nag_runner.json"),
        ]

        for config_file in possible_config_files:
            if os.path.exists(config_file):
                return config_file

        possible_config_files_string = ", ".join(possible_config_files)
        raise MissingConfigException(
            f"No config file found in {possible_config_files_string}"
        )

    def get_default_last_run_path(self):
        "Returns the default path to the last run file."
        return os.path.join(
            os.path.expanduser("~"), ".cache", "nag_runner", "last_run.json"
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

    def set_last_run(self, name):
        "Sets the last run time for a command."
        last_run = {}
        if os.path.exists(self.last_run_path):
            with open(self.last_run_path, "r", encoding="utf-8") as file:
                last_run = json.load(file)
        else:
            os.makedirs(os.path.dirname(self.last_run_path), exist_ok=True)
        last_run[name] = datetime.now().isoformat()
        with open(self.last_run_path, "w", encoding="utf-8") as file:
            json.dump(last_run, file)

    def get_entry_by_name(self, name):
        "Returns the entry with the given name."
        for entry in self.config:
            if entry.name == name:
                return entry
        return None

    def run_entry(self, entry):
        "Runs the given entry."
        call(entry.command, shell=True)
        self.set_last_run(entry.name)

    def run_entry_by_name(self, name):
        "Runs the entry with the given name."
        entry = self.get_entry_by_name(name)
        if not entry:
            raise InvalidEntryException(f"Could not find entry with name {name}")
        self.run_entry(entry)

    def print_menu(self):
        "print the help menu"

        print(
            """
        Possible responses are:
        y: Run the command
        n: Do not run the command, but still nag me next time
        d: don't run the command this time and reset the interval. This is useful if
            you've  run the command outside of nag_runner recently
        ?: Show this help message
        """
        )

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
                    f"Run now? [Y/n/d/?] "
                )
            else:
                prompt = f"You have never run {entry.name}. Run now? [Y/n/d/?] "

            response = None
            while not response:
                print(prompt, end="")
                response = input()
                if response == "?":
                    self.print_menu()
                    response = None

            if response in ["y", "Y", ""]:
                self.run_entry(entry)
            elif response == "d":
                self.set_last_run(entry.name)
            else:
                print("Ok, I'll nag you next time")


def main():
    "Main function."
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-path", "-c", help="Path to the config file")
    parser.add_argument("--last-run-path", "-l", help="Path to the last run file")
    parser.add_argument("--name", "-n", help="Name of a single entry to run")
    args = parser.parse_args()

    nag_runner = NagRunner(args.config_path, args.last_run_path)

    if args.name:
        nag_runner.run_entry_by_name(args.name)
        return
    nag_runner.run_overdue_entries()


if __name__ == "__main__":
    try:
        main()
    except NagRunnerException as e:
        print(e)
        sys.exit(1)

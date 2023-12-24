#!/usr/bin/python3
"Nag Runner: Reminds you to run important commands on a regular basis."

import argparse
import json
import os
import sys
from collections import namedtuple
from datetime import datetime
from subprocess import call


Entry = namedtuple("Entry", ["name", "command", "interval"])


class NagRunner:
    "main class for nag runner."

    def __init__(self, config_path, last_run_path=None):
        self.config = self.load_config(config_path)
        self.last_run_path = last_run_path or os.path.expanduser(
            "~/.cache/nag_runner/last_run.json"
        )
        self.choice_methods = [
            getattr(self, method_name)
            for method_name in dir(self)
            if method_name.startswith("choice_")
        ]

    def load_json_file(self, path, default):
        "Loads a json file from the given path."
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

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
            entries = self.load_json_file(possible_config_file, [])
            if entries:
                return [Entry(**entry_data) for entry_data in entries]
        sys.exit(f"No config file found at {', '.join(possible_config_files)}")

    def get_days_since_last_run(self, entry):
        "Returns the number of days since the command was last run."
        last_run_dict = self.load_json_file(self.last_run_path, {})
        if entry.name not in last_run_dict:
            return None
        last_run_time = datetime.strptime(
            last_run_dict[entry.name], "%Y-%m-%dT%H:%M:%S.%f"
        )
        return (datetime.now() - last_run_time).days

    def get_days_to_next_run(self, entry):
        "Returns the number of days until the command should be run."
        days_since = self.get_days_since_last_run(entry)
        return 0 if days_since is None else int(entry.interval) - days_since

    def get_entry_by_name(self, name):
        "Returns the entry with the given name."
        for entry in self.config:
            if entry.name == name:
                return entry
        sys.exit(f"Could not find entry with name {name}")

    def get_entry_info(self, entry, show_extras):
        "gets the entry's name, when it will next run, and how often it runs."
        info = [entry.name]
        days_since = self.get_days_since_last_run(entry)
        if days_since is None:
            info.append(" has never run before.")
        else:
            info.append(f" was last run {days_since} days ago.")
        if show_extras:
            info.append(" It runs next in ")
            info.append(f"{max(self.get_days_to_next_run(entry), 0)} days.")
            info.append(f" It runs every {entry.interval} days.")
        return "".join(info)

    def run_entry_by_name(self, name):
        "Runs the entry with the given name."
        self.run_entry(self.get_entry_by_name(name))

    def run_overdue_entries(self):
        "Runs all overdue entries."
        for entry in self.config:
            days_since = self.get_days_since_last_run(entry)
            if days_since is not None:
                if days_since < int(entry.interval):
                    continue
            self.run_choice(f"{self.get_entry_info(entry, False)} Run now?", entry)

    def run_entry(self, entry):
        "Y: Runs the command and set it's last run date."
        call(entry.command, shell=True)
        self.set_last_run(entry)

    choice_1_run_entry = run_entry

    def choice_2_print_next_time_message(self, _entry):
        "n: Do not run the command, but still nag me next time."
        print("Ok, I'll nag you next time")

    def set_last_run(self, entry):
        "d: Don't run the command, but pretend we did."
        os.makedirs(os.path.dirname(self.last_run_path), exist_ok=True)
        last_run = self.load_json_file(self.last_run_path, {})
        last_run[entry.name] = datetime.now().isoformat()
        with open(self.last_run_path, "w", encoding="utf-8") as file:
            json.dump(last_run, file)

    choice_3_set_last_run = set_last_run

    def choice_4_print_menu(self, _entry):
        "?: Show the help menu"
        print("Possible responses are:")
        for method in self.choice_methods:
            print(method.__doc__)

    def run_choice(self, prompt, entry):
        "Gets the user's choice and runs the appropriate action."
        while True:
            choice_letters = [method.__doc__[0] for method in self.choice_methods]
            response = input(f"{prompt} [{'/'.join(choice_letters)}] ").lower()
            for method in self.choice_methods:
                if method.__doc__[0].lower() == response or (
                    method.__doc__[0].isupper() and response == ""
                ):
                    method(entry)
                    if method.__doc__[0] != "?":
                        return


if __name__ == "__main__":
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
        for config_entry in nag_runner.config:
            print(nag_runner.get_entry_info(config_entry, True))
    else:
        nag_runner.run_overdue_entries()

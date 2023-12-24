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
        if days_since is None:
            return 0

        return int(entry.interval) - days_since

    def get_entry_by_name(self, name):
        "Returns the entry with the given name."
        for entry in self.config:
            if entry.name == name:
                return entry
        sys.exit(f"Could not find entry with name {name}")

    def list_entries_next_run(self):
        "Lists all entries and when they will next run."
        for entry in self.config:
            days_until_next_run = max(self.get_days_to_next_run(entry), 0)
            days_since = self.get_days_since_last_run(entry)
            runs_every_text = f"Runs every {entry.interval} days"
            next_run_text = f"Next run in {days_until_next_run} days"
            last_run_text = "never run before"
            if days_since is not None:
                last_run_text = f"last run {days_since} days ago"

            print(f"{entry.name}: {next_run_text} ({runs_every_text}, {last_run_text})")

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
        os.makedirs(os.path.dirname(self.last_run_path), exist_ok=True)
        last_run = self.load_json_file(self.last_run_path, {})
        last_run[entry.name] = datetime.now().isoformat()
        with open(self.last_run_path, "w", encoding="utf-8") as file:
            json.dump(last_run, file)

    def print_next_time_message(self, _entry):
        "Do not run the command, but still nag me next time."
        print("Ok, I'll nag you next time")

    def print_menu(self, _entry):
        "Show the help menu"
        print("Possible responses are:")
        for responses, method, _ask_again in self.get_user_actions():
            print(f"{responses[0]}: {method.__doc__}")

    def get_user_actions(self):
        "Returns a list of actions the user can take."
        return [
            # (responses, method, ask_again)
            (["Y", "y", ""], self.run_entry, False),
            (["n", "N"], self.print_next_time_message, False),
            (["d"], self.set_last_run, False),
            (["?"], self.print_menu, True),
        ]

    def run_overdue_entries(self):
        "Runs all overdue entries."
        actions = self.get_user_actions()
        choice_letters = [responses[0] for responses, _, _ in actions]
        run_now_text = f"Run now? [{'/'.join(choice_letters)}] "

        for entry in self.config:
            days_since = self.get_days_since_last_run(entry)
            if days_since is not None:
                if days_since < int(entry.interval):
                    continue

                days_since_text = (
                    f"It has been {days_since} days since you last ran {entry.name}."
                )
                prompt = f"{days_since_text} {run_now_text}"
            else:
                prompt = f"You have never run {entry.name}. {run_now_text}"

            keep_going = True
            while keep_going:
                print(prompt, end="")
                response = input()
                for responses, method, ask_again in actions:
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
    main()

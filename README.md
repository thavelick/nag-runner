# Nag Runner

Reminds you to run important commands on a regular basis.

This is useful to use on a system like a laptop that you don't leave running all the time to run things that you might otherwise throw in a cron.

## Installation and Usage

1. Clone
```bash
git clone https://github.com/thavelick/nag-runner.git
```
2. Make a config file
```bash
cat <<  EOF > ~/.config/nag_runner.json
[
    {
        "name": "archlinux updates",
        "command": "sudo pacman -Syu",
        "interval": "1" // Number of days to wait before nagging again
    }
]
EOF
```
3. Make it run whenever you start a shell
```bash
echo $(pwd)/nag_runner.py >> ~/.zshrc
```
4. Now when you open a new terminal you'll see something like this:
```
You've never run archlinux updates. Run now? [Y/n/d/?]? ?
Possible responses are:
    y: Run the command
    n: Do not run the command, but still nag me next time
    d: don't run the command this time and reset the interval. This is useful if
         you've  run the command outside of nag_runner recently
    ?: Show this help message
You've never run archlinux updates. Run now? [Y/n/d/?]? ? y
[...output from pacman...]
```
If you open another terminal you won't see another nag until the interval has
passed.

## Arguments
* `--config-path`, `-c`: Path to config file. Defaults to `~/.config/nag_runner.json` or `./nag_runner.json`.
* `--last-run-path`, `-l`: Path to the last run file.
* `--name`, `-n`: Name of a single entry to run.
* `--list`: List all entries and when they will next run. Will output something like this:
```
archlinux updates: Next run in 7 days (Runs every 7 days, last run 0 days ago)
prune yay cache: Next run in 21 days (Runs every 31 days, last run 10 days ago)
prune backups: Next run in 32 days (Runs every 37 days, last run 5 days ago)
backups: Next run in 8 days (Runs every 11 days, last run 3 days ago)
```
* `--check`: Check if there are any overdue entries. Exits with code 0 if no entries are overdue, or code 1 if entries need to be run. Useful for scripts:
```bash
if ! ./nag_runner.py --check; then
    echo "Running overdue nags..."
    ./nag_runner.py
fi
```

## Tips
* If you'd like each different commands to run on different days, set each interval to a prime number of days. For instance if you set one command to run every 11 days and another every 13 days, they'll run with roughly the same regularity, but never on the same day.
* Conversely if I choose intervals that share a lot of common factors, you can tend to batch things together while running them with different frequencies.

### Some ideas on what to run with Nag Runner
I use this to regularly run scripts that:
* Update my system's packages
* Prune caches
* Run and prune backups
* Rotate credentials and API keys that expire

## Dependencies
* Python 3

## Created By
* [Tristan Havelick](https://tristanhavelick.com)

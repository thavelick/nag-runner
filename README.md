# Nag Runner

Reminds you to run important commands on a regular basis.

## Installation and Usage

1. Clone
```bash
git clone https://github.com/thavelick/nag-runner.git && cd nag-runner
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
archlinux updates: Next run in 6 days
prune yay cache: Next run in 20 days
``````

## Dependencies
* Python 3

## Created By
* [Tristan Havelick](https://tristanhavelick.com)

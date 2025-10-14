# Daemon for Echolalia
A Python-based daemon that periodically checks and schedules tasks from Echolalia

## Running the Daemon
Create a virtual environment somewhere, or use your Conda environment, and just install the project

```bash
pip install git@github.com:LAAC-LSCP/analysis-daemon.git
run-daemon [path to configuration toml file]
```

Note you need to have an ssh key associated with LAAC.

For updating the DB

```bash
run-migrations [path to configuration toml file]
```

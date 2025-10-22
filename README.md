# Daemon for Echolalia
A Python-based daemon that periodically checks and schedules tasks from Echolalia

## Running the Daemon
Create a virtual environment somewhere, or use your Conda environment, and just install the project

```bash
pip install git@github.com:LAAC-LSCP/analysis-daemon.git
echolalia --config [path to configuration toml file] run-daemon
```

Note you need to have an ssh key associated with LAAC.

For updating the DB

```bash
echolalia --config [path to configuration toml file] run-migrations
```

## Configuration

An example configuration is given below for configuration.toml.

You'll need to create a file like this on your own system.

```
[database]
url = "sqlite:///database.db"

[http]
base_url = "ECHOLALIA_REMOTE_SERVER_URL"
client_id = "MY_ID"
client_secret = "SECRET"

[jobs]
handler = "slurm"
partition = "echolalia"

[[filesystems]]
dataset_name = "dataset_1"
path = "/Users/me/Desktop/datasets/dataset_1"

  [[filesystems.scripts]]
  script_name = "run_vtc"
  script_path = "scripts/run_vtc.py"
  model_name = "vtc"

[[filesystems]]
dataset_name = "dataset_2"
path = "/Users/me/Desktop/datasets/dataset_2"

  [[filesystems.scripts]]
  script_name = "run_vtc"
  script_path = "scripts/run_vtc.py"
  model_name = "vtc"
```
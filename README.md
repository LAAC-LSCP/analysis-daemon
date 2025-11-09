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

To manage tasks directly from the CLI, say for bug-fixing purposes, see
```bash
echolalia --config [path to configuration toml file] task-manager --help
```

## Configuration

An example configuration is given below for configuration.toml.

You'll need to create a file like this on your own system. Note that file paths should be absolute, not relative paths.

```
log_directory = "/Users/me/Desktop/echolalia_log"

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

[[filesystems]]
dataset_name = "dataset_2"
path = "/Users/me/Desktop/datasets/dataset_2"

[[scripts]]
name = "run_vtc"
path = "/Users/me/Desktop/scripts/run_vtc.py"
model = "vtc"

[[scripts]]
name = "run_vcm"
script = "/Users/me/Desktop/scripts/run_vcm.py"
model = "vcm"

[[scripts]]
name = "run_alice"
script = "/Users/me/Desktop/scripts/run_alice.py"
model = "alice"
```

## Script Setup (READ CAREFULLY!)
It is recommended you use the scripts from the scripts folder in the repo.

While working on this system, we realised we couldn't run a per-file slurm job, for example running vtc on a per-file basis by launching a new job for each file. This was due to memory requirements. While the smaller models could use this pattern, W2V2 presented a problem because it was 1) very large and 2) designed to be run over countless tiny files—as a result, the cost of bootstrapping the model each time would have been too high.

We have opted for a compromise that has a few anti-patterns and requires careful reading, if you want to add new scripts that is. The daemon, instead of asking SLURM for status updates, will continuously check a log file created by the running script. Running scripts must, therefore, take in a log directory. Scripts are assumed, by the daemon, to adhere to a strict interface that looks something like:

```bash
python3 vtc.py --task-id [task id] --bash-script [the .sh script used by the model] --input-folder [input_dir] --output-folder [output_dir] -i [file 1] -i [file 2] ...
```

Finally, for running any of the models, you must install the associated Conda environments. More info on getting the models to work at:

https://github.com/MarvinLvn/voice-type-classifier/ for VTC
https://github.com/orasanen/ALICE for ALICE
https://github.com/LAAC-LSCP/vcm/ for VCM

Each model has its own corresponding Conda environment.

Note that since the Python wrapper scripts rely on some libraries as well (typically only `click` is missing) some dependencies may be missing. You just need to `pip install` them into your Conda environments, or change the conda env files to include them.


# Daemon for Echolalia
A Python-based daemon that periodically checks and schedules tasks from Echolalia

## Development
We use poetry for package and dependency management. You can install poetry system-wide with pipx:

```bash
pipx install poetry
```

Conda does not always play well with other package managers, so conda may need to be deactivated (not only the conda environment) during development.

To lock and install dependencies run

```bash
poetry install
poetry lock
```

To enter the Python virtual environment run

```bash
eval $(poetry env activate)
```

Note this doesn't spawn a subshell, so `exit` will close your shell entirely. You could use the poetry shell plugin for more control. Finally, it is important to enter the virtual environment before installing dependencies.

To build the project just run

```bash
poetry build
```

And the source and binary distributions will appear in the `dist/` folder.

## Running the Daemon
Create a virtual environment somewhere, or use your Conda environment, and just install the project

```bash
pip install git@github.com:LAAC-LSCP/analysis-daemon.git
run-daemon
```

Note you need to have an ssh key associated with LAAC.

## Testing
Run pytest as usual. In the root of the project run
```bash
pytest
```

To run the tests in various fresh virtual environments you can use tox. You can install tox via pipx `pipx install tox`.

And tox tests in python 3.13 can be run with, say
```bash
tox -e py313 -- --randomly-seed=1234
```
The seed is optional, and will shuffle the order of the tests and is good practice.
To run the full suite with linting, formatting and type-checking, you will need to install black, isort, autoflake, flake8 and mypy with pipx, and run `tox`.

## Working with the Daemon and source maps
Within your environment, Conda or otherwise, use the `--editable` option to install the Daemon with the source maps

```bash
pip install -e [path]
```

Then your dependency updates with the changes made locally, and even debugging and IntelliSense will work.

## Commits and Semantic Versioning
We bump our releases and update our changelog automatically, but this requires commits to follow the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) scheme. We use a combination of [release-please](https://github.com/googleapis/release-please) and [commitlint](https://commitlint.js.org/).

We recommend using squash-merge for pull requests for many reasons. Rebase-merge works too, but if you're doing something like red/green development, or did not validate all your individual commits against the actions, the main branch may not be clean after a rebase-merge (in the sense that every snapshot be clean).
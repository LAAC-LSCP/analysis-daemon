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
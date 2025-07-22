A Python-based daemon that periodically checks and schedules tasks from Echolalia

# Development
We use poetry for package and dependency management. You can install poetry system-wide with pipx:

`pipx install poetry`

Conda does not always play well with other package managers, so conda may need to be deactivated (not only the conda environment) during development.

To install dependencies run

`poetry install`

To lock dependencies to specific versions run

`poetry lock`

To enter the Python virtual environment run

`poetry shell`

To build the project just ru

`poetry build`

And the source and binary distributions will appear in the `dist/` folder.
# Contributing to the Daemon
For those interested in developing for the analysis-service, below I share ways to get started and some of the conventions we use.

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

If a suitable Python version cannot be found, it's recommended to use `pyenv` to install it, e.g., `pyenv install 3.13.0`.

Note this doesn't spawn a subshell, so `exit` will close your shell entirely. You could use the poetry shell plugin for more control. Finally, it is important to enter the virtual environment before installing dependencies.

To build the project just run

```bash
poetry build
```

And the source and binary distributions will appear in the `dist/` folder.

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

## Lint and Typecheck Locally
Install `black`, `isort`, `autoflake`, `flake8`, `mypy`, system-wide with `pipx` or in your environment with `pip`. Go to the repository root and run `black .`, `isort .`, `autoflake .`, `flake8 .` and `mypy .` to lint/format/type-check.

## Commits and Semantic Versioning
We bump our releases and update our changelog automatically, but this requires commits to follow the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) scheme. We use a combination of [release-please](https://github.com/googleapis/release-please) and [commitlint](https://commitlint.js.org/).

We recommend using squash-merge for pull requests for many reasons. Rebase-merge works too, but if you're doing something like red/green development, or did not validate all your individual commits against the actions, the main branch may not be clean after a rebase-merge (in the sense that every snapshot be clean).

```note
Note: if squashing or rebasing, the commit message must conform to commitlint's rules, otherwise release-please will not create a PR. Furthermore, once the PR is created, it must be manually merged due to branch protection rules (no need to do anything more). TODO: If we had a bot set up with permission to merge to main, 
```

## Migrations
The database may change over time, whether for reasons of data or schema. Either way, we depend on alembic to handle migrations. We initialise the database through a migration. We have wrapped our alembic logic in a command

```bash
run-migrations
```

## Architecture
The daemon is a single event-driven, monolithic microservice. We chose events and commands for their natural translation to tasks, and their loose coupling and easy logging. The domain objects that the service deals with are 

1. Tasks - tasks, such as "run the voice type classifier model over the dataset Loann-2025 for user "Lawrence""
2. Commands - things to do to a task, such as running a task, completing a task, etc.
3. Events - events that have happened, such as a task being started, or being completed, or an error say

Tasks are unique in that they are communicated over the network with Echolalia, and so the network definition in `response_types.py` is separate from the domain-definition in `model.py`. This is important to keep in mind.

The architecture is thinly layered, with a DB, domain, and service layer.
1. The database layer is the DB itself and the adapters, such as the ORM, followed by the repository pattern
2. The domain layer is a thin layer with the domain object definitions, such as tasks, commands and events
3. The service layer contains the application logic, such as the event/command queues and message broker, the bootstrapper/composition root, and command and event handlers

### The Main Algorithm
The daemon is activated with the `run_daemon` command, running the bootstrap function which returns a full `Service`—which acts as a composition root—that contains a single `HTTPClient` and unit of work. It also loads the config and sets up logging.

The service object is designed to be as testable as possible. It acts in an application loop, thus ticking and with each tick:
1. Calls Echolalia to obtain new tasks
2. Puts these on the message broker

The message broker routes the messages to the event or command queues. The queues themselves also tick, and are on their own very testable. But importantly, these queues are run on their own threads, and so tick "out of sync" with the service, but there are no shared resources between the main service thread and the queues themselves to worry about. A queue is actually a wrapper around an `asyncio` queue, which runs task after task greedily as they are being added. A queue in our sense can actually have tasks waiting in line, and with each tick the queue
1. Calculate current workload of active tasks
2. Calculate waiting task priorities
3. If ready, move task from the waiting line to be run

To get a good sense of the lifecycle of a task, and the intended programming pattern, it's important to get into an "event-storming" mindset. A task is actually the result of a `CreateTask` command, which in turn can spawn a `RunTask` command if handled, and a `TaskStarted` event, say. In this way tasks actually live as commands spawning off children and events.
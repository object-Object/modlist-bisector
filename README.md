# modlist-bisector

Minecraft modlist bisector to help track down bugs.

## Algorithm

This project is based on the Binary Reduction algorithm from the following paper:

Christian Gram Kalhauge and Jens Palsberg. 2019. Binary reduction of dependency graphs. In Proceedings of the 2019 27th ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE 2019). Association for Computing Machinery, New York, NY, USA, 556–566. https://doi.org/10.1145/3338906.3338956

## Usage

> [!CAUTION]
> DependencyGrapher currently only works on Fabric and Quilt. Sinytra Connector is not supported ([#4](https://github.com/object-Object/modlist-bisector/issues/4)).

1. Add the [companion mod DependencyGrapher](./DependencyGrapher) to the game instance you want to debug.
2. Start the game with DependencyGrapher enabled. It should generate a file in the game instance's `.minecraft` folder called `dependencygrapher.json`.
3. Disable or remove DependencyGrapher. It excludes itself from the dependency graph it generates, so you may encounter errors if any of its dependencies are disabled.
4. [Install uv](https://docs.astral.sh/uv/getting-started/installation/); then clone this repository, open it in a terminal, and run `uv sync` to initialize the Python tool.
5. Run `uv run bisect start path/to/dependencygrapher.json`.
   * If there are specific mods you want to keep enabled at all times, you can use the `-r` flag for each modid. For example: `uv run bisect start path/to/dependencygrapher.json -r hexcasting -r create`
6. Start the game and attempt to reproduce the issue, then close the game.
7. Run `uv run bisect good` or `uv run bisect bad`, depending if the issue occurred or not.
8. Repeat steps 6-7 until the bisector finds a minimal modlist to reproduce the issue.
9. To clean up, run `uv run bisect reset` to reenable all mods.

## Development

This project is managed by [uv](https://docs.astral.sh/uv/). To get started with contributing to modlist-bisector, [install uv](https://docs.astral.sh/uv/getting-started/installation/), then run the following commands:

```sh
uv sync
uv run pre-commit install
```

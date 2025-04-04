# modlist-bisector

Minecraft modlist bisector to help track down bugs.

## Algorithm

This project is based on the Binary Reduction algorithm from the following paper:

Christian Gram Kalhauge and Jens Palsberg. 2019. Binary reduction of dependency graphs. In Proceedings of the 2019 27th ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE 2019). Association for Computing Machinery, New York, NY, USA, 556–566. https://doi.org/10.1145/3338906.3338956

## Project structure

This project is managed by [Rye](https://rye.astral.sh). To get started, [install Rye](https://rye.astral.sh/guide/installation), then run the following commands:

```sh
rye sync
rye run pre-commit install
```

## Usage

1. Add the companion mod DependencyGrapher to the game instance you want to debug.
2. Start the game with DependencyGrapher enabled. It should generate a file in the game instance's `.minecraft` folder called `dependencygrapher.json`.
3. Disable or remove DependencyGrapher. It excludes itself from the dependency graph it generates, so you may encounter errors if any of its dependencies are disabled.
4. Run `rye run bisect start path/to/dependencygrapher.json`.
5. Start the game and attempt to reproduce the issue.
6. Run `rye run bisect good` or `rye run bisect bad`, depending if the issue occurred or not.
7. Repeat steps 5-6 until the bisector finds a minimal modlist to reproduce the issue.

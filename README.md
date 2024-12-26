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

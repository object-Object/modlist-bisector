from pathlib import Path
from textwrap import dedent

from typer import Typer

from .mod_graph import ModGraph

DEFAULT_CONFIG_PATH = Path("config.toml")


app = Typer(pretty_exceptions_enable=False)


@app.command()
def start(*, reset: bool = True, config_path: Path = DEFAULT_CONFIG_PATH):
    ModGraph.build(config_path, reset=reset).bisect().save()


@app.command()
def reset(*, config_path: Path = DEFAULT_CONFIG_PATH):
    ModGraph.build(config_path, reset=True).save()


@app.command()
def status(*, list_remaining: bool = False, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load(config_path)
    enabled, disabled, total = G.count_nodes()
    print(
        dedent(
            f"""\
            Enabled:  {enabled}
            Disabled: {disabled}
            Locked:   {total - enabled - disabled}
            Total:    {total}"""
        )
    )

    if list_remaining:
        for node in G.pending_nodes().values():
            print(node["name"])


@app.command()
def good(*, config_path: Path = DEFAULT_CONFIG_PATH):
    print(
        "Swapping enabled and disabled mods. If the next step is also good, "
        "there's a conflict somewhere between the last two modlists."
    )
    ModGraph.load(config_path).set_enabled_good().save()


@app.command()
def bad(*, config_path: Path = DEFAULT_CONFIG_PATH):
    ModGraph.load(config_path).set_disabled_good().bisect().save()


@app.command()
def enable(modid: str, *, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load(config_path)
    if G.enable(modid):
        print(f"Enabled {modid}.")
    else:
        print(f"{modid} was already enabled.")
    G.save()


@app.command()
def disable(modid: str, *, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load(config_path)
    if G.disable(modid):
        print(f"Disabled {modid}.")
    else:
        print(f"{modid} was already disabled.")
    G.save()


if __name__ == "__main__":
    app()

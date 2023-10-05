from pathlib import Path
from textwrap import dedent

from typer import Typer

from .mod_graph import ModGraph

DEFAULT_CONFIG_PATH = Path("config.toml")


app = Typer(pretty_exceptions_enable=False)


@app.command()
def start(*, reset: bool = True, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load_mods(config=config_path)
    G.assert_acyclic_pending()

    if reset:
        for modid in G.nodes:
            G.enable(modid)

    G.bisect()
    G.dump_file()


@app.command()
def reset(*, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load_mods(config=config_path)
    for modid in G.nodes:
        G.enable(modid)
    G.dump_file()


@app.command()
def status(*, list_remaining: bool = False, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load_file(config=config_path)
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
    G = ModGraph.load_file(config=config_path)
    G.set_enabled_good()
    G.bisect()
    G.dump_file()


@app.command()
def bad(*, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load_file(config=config_path)
    G.set_disabled_good()
    G.bisect()
    G.dump_file()


@app.command()
def required(modid: str, *, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load_file(config=config_path)
    G.enable(modid)
    G.set_good(modid, True)
    G.dump_file()


@app.command()
def dependency(modid: str, dependency: str, *, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load_file(config=config_path)

    assert modid in G.nodes and dependency in G.nodes
    G.G.add_edge(modid, dependency)

    if G.node(modid)["enabled"] and not G.node(dependency)["enabled"]:
        G.set_good(dependency, None)
        G.enable(dependency)

    G.dump_file()


@app.command()
def enable(modid: str, *, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load_file(config=config_path)
    if G.enable(modid):
        print(f"Enabled {modid}.")
    else:
        print(f"{modid} was already enabled.")
    G.dump_file()


@app.command()
def disable(modid: str, *, config_path: Path = DEFAULT_CONFIG_PATH):
    G = ModGraph.load_file(config=config_path)
    if G.disable(modid):
        print(f"Disabled {modid}.")
    else:
        print(f"{modid} was already disabled.")
    G.dump_file()


if __name__ == "__main__":
    app()

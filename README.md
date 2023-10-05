# modlist-bisector
Minecraft modlist bisector to help track down bugs.

## Example `config.toml`

```toml
root = "C:/Users/object/AppData/Roaming/PrismLauncher/instances/HexxyCraft/.minecraft/mods"

required = [
    "quilted_fabric_api",
    "cardinal-components",
    "create",

    # import cycles :(
    "sodium",
    "indium",
]

[extra_deps]
switchy = ["owo"]
ding = ["completeconfig"]
balm-fabric = ["cloth-config"]
emi = ["polymer-all"]
```

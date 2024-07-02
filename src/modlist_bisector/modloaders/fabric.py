from pathlib import Path
from typing import Annotated, Any, Literal, override

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    UrlConstraints,
    model_validator,
)
from pydantic.alias_generators import to_camel

from modlist_bisector.utils.types import cast_nullable

from .base import Mod


class _FabricModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        alias_generator=to_camel,
    )


type Environment = Literal["*", "client", "server"]
"""For games with multiple environments - is a string value defining an environment
the mod should be considered for loading on.

Supported values are:

* `*` - all environments (default)
* `client` - the game client
* `server` - the game dedicated server (integrated servers are not included here)
"""


type EnvironmentField = Environment | list[Environment]
"""For games with multiple environments - is a string value (or an array of string
values) defining the environments the mod should be considered for loading on."""


class ContactInformation(_FabricModel):
    """A string→string dictionary containing contact information.

    There are no mandatory keys.

    The list is not exhaustive - mods may provide additional, non-standard keys (such as
    discord, slack, twitter) - if possible, they should be valid URLs.

    https://fabricmc.net/wiki/documentation:fabric_mod_json_spec
    """

    email: EmailStr | None = None
    """Contact e-mail pertaining to the mod.

    Must be a valid e-mail address.
    """
    irc: Annotated[AnyUrl, UrlConstraints(default_port=6667)] | None = None
    """IRC channel pertaining to the mod.

    Must be of a valid URL format - for example: `irc://irc.esper.net:6667/charset` for
    #charset at EsperNet - the port is optional, and assumed to be 6667 if not present.
    """
    homepage: HttpUrl | None = None
    """Project or user homepage.

    Must be a valid HTTP/HTTPS address.
    """
    issues: HttpUrl | None = None
    """Project issue tracker.

    Must be a valid HTTP/HTTPS address.
    """
    sources: AnyUrl | None = None
    """Project source code repository.

    Must be a valid URL - it can, however, be a specialized URL for a given VCS (such as
    Git or Mercurial).
    """


class Entrypoint(_FabricModel):
    """An object representing an entrypoint in `EntrypointContainer`.

    https://fabricmc.net/wiki/documentation:fabric_mod_json_spec
    """

    adapter: str = "default"
    """Optional key denoting the language adapter to use."""
    value: str
    """The default language adapter uses this specific key as a string value of any of
    the following formats:

    * `my.package.MyClass`, which points to a class to be instantiated,
    * `my.package.MyClass::thing`, which points to a static field (contents returned) or
    method handle (for interface types, proxied automatically) named `thing`.
    """

    @model_validator(mode="before")
    @classmethod
    def _validate_str(cls, value: Any):
        if isinstance(value, str):
            return {"value": value}
        return value


type EntrypointContainer = dict[str, list[Entrypoint]]
"""An EntrypointContainer is an object.

The keys match the getEntrypoints() `type` field, and are the type of the entrypoints to
be listed - `main`, `client`, `server`. The values of those keys are arrays, containing
either strings (of the object key `value`'s value) or `Entrypoint` objects.

https://fabricmc.net/wiki/documentation:fabric_mod_json_spec
"""


class NestedJarEntry(_FabricModel):
    """https://fabricmc.net/wiki/documentation:fabric_mod_json_spec"""

    file: Path
    """A string value pointing to a path from the root of the mod to a nested JAR which
    should be loaded alongside the outer mod JAR."""


class Person(_FabricModel):
    """https://fabricmc.net/wiki/documentation:fabric_mod_json_spec"""

    name: str
    """The real name, or username, of the person."""
    contact: ContactInformation | None = None
    """Contact information pertaining to the person."""

    @model_validator(mode="before")
    @classmethod
    def _validate_str(cls, value: Any):
        if isinstance(value, str):
            return {"name": value}
        return value


type VersionRange = str | list[str]
"""A string or array of strings declaring supported version ranges in the form
`<operator1><range1>[ <operator2><range2>]...`.

Multiple space separated ranges within the same string follow an “AND” relationship -
they must all be satisfied. In the case of an array, an “OR” relationship is assumed
between the array elements - that is, only one element has to match for the collective
declaration to be satisfied.

https://fabricmc.net/wiki/documentation:fabric_mod_json_spec
"""


class Mixin(_FabricModel):
    """A mixin configuration file for the Mixin library.

    https://fabricmc.net/wiki/documentation:fabric_mod_json_spec
    """

    config: Path
    """Filename relative to the mod root."""
    environment: EnvironmentField = "*"

    @model_validator(mode="before")
    @classmethod
    def _validate_str(cls, value: Any):
        if isinstance(value, (str, Path)):
            return {"config": value}
        return value


class FabricModFile(_FabricModel):
    """A `fabric.mod.json` file (Version 1).

    https://fabricmc.net/wiki/documentation:fabric_mod_json_spec
    """

    schema_version: Literal[1]
    """An integer value, denoting the version of the format."""

    # Mandatory fields

    id: str = Field(pattern=r"^[a-z][a-z0-9-_]{1,63}$")
    """Contains the mod identifier.

    A string value matching the `^[a-z][a-z0-9-_]{1,63}$` pattern.
    """
    version: str
    """Contains the mod version.

    A string value, optionally matching the [Semantic Versioning 2.0.0](https://semver.org/)
    specification.
    """

    # Optional fields (mod loading)

    environment: EnvironmentField = "*"
    """For games with multiple environments - is a string value (or an array of string
    values) defining the environments the mod should be considered for loading on."""
    entrypoints: EntrypointContainer = Field(default_factory=dict)
    """Contains an EntrypointContainer."""
    jars: list[NestedJarEntry] = Field(default_factory=list)
    """Contains an array of NestedJarEntry objects."""
    language_adapters: dict[str, str] = Field(default_factory=dict)
    """A string→string dictionary, connecting namespaces to LanguageAdapter
    implementations."""
    mixins: list[Mixin] = Field(default_factory=list)
    """Contains a list of mixin configuration files for the Mixin library."""
    access_widener: Path | None = None
    """A file path to an [access widener](https://fabricmc.net/wiki/tutorial:accesswideners)
    relative to the mod root.

    If not present, assume the mod has no access widener.
    """

    # Optional fields (dependency resolution)

    depends: dict[str, VersionRange] = Field(default_factory=dict)
    """For these dependencies, a failure to match causes a hard failure.

    A string→VersionRange dictionary, where the string key matches the desired ID.
    """
    recommends: dict[str, VersionRange] = Field(default_factory=dict)
    """For these dependencies, a failure to match causes a soft failure (warning).

    A string→VersionRange dictionary, where the string key matches the desired ID.
    """
    suggests: dict[str, VersionRange] = Field(default_factory=dict)
    """These dependencies are not matched and are primarily used as metadata.

    A string→VersionRange dictionary, where the string key matches the desired ID.
    """
    conflicts: dict[str, VersionRange] = Field(default_factory=dict)
    """For these dependencies, a successful match causes a soft failure (warning).

    A string→VersionRange dictionary, where the string key matches the desired ID.
    """
    breaks: dict[str, VersionRange] = Field(default_factory=dict)
    """For these dependencies, a successful match causes a hard failure.

    A string→VersionRange dictionary, where the string key matches the desired ID.
    """

    # Optional fields (metadata)

    name: str = Field(default=None, validate_default=False)
    """Contains the user-facing mod name. If not present, assume it matches `id`."""
    description: str = ""
    """Contains the user-facing mod description."""
    authors: list[Person] = Field(default_factory=list)
    """Contains the direct authorship information."""
    contributors: list[Person] = Field(default_factory=list)
    """Contains the contributor information."""
    contact: ContactInformation | None = None
    """Contains the contact information for the project."""
    license: str | list[str] | None = None
    """Contains the licensing information.

    This should provide the complete set of preferred licenses conveying the entire mod
    package. In other words, compliance with all listed licenses should be sufficient
    for usage, redistribution, etc. of the mod package as a whole.

    For cases where a part of code is dual-licensed, choose the preferred license. The
    list is not exhaustive, serves primarily as a kind of hint, and does not prevent you
    from granting additional rights/licenses on a case-by-case basis.
    """
    icon: Path | dict[str, Path] | None = None
    """Contains the mod's icon, as a square .PNG file.

    (Minecraft resource packs use 128x128, but that is not a hard requirement - a power
    of two is, however, recommended.)

    Can be provided in one of two forms:

    * A string, providing the path (from the mod's root) to a single .PNG file.
    * A string→string dictionary, where the keys conform to widths of each PNG file,
    and the values are said files' paths.
    """

    @model_validator(mode="after")
    def _set_default_name(self):
        if cast_nullable(self.name) is None:
            self.name = self.id
        return self


class FabricMod(Mod[FabricModFile], modloader="fabric", meta_path="fabric.mod.json"):
    @classmethod
    @override
    def load_meta(cls, data: str):
        return FabricModFile.model_validate_json(data)

    @property
    @override
    def id(self):
        return self.meta.id

    @property
    @override
    def name(self):
        return self.meta.name

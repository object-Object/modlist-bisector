from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class _QuiltModel(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )


MAVEN_GROUP_PATTERN = r"(?!loader\.plugin\.)[a-zA-Z0-9-_.]+"

MOD_ID_PATTERN = r"[a-z][a-z0-9-_]{1,63}"


type MavenGroup = Annotated[
    str,
    Field(pattern=f"^{MAVEN_GROUP_PATTERN}$"),
]
"""A Maven group id.

A unique identifier for the organization behind or developers of the mod. The group
string must match the `^[a-zA-Z0-9-_.]+$` regular expression, and must not begin with
the reserved namespace `loader.plugin.` It is recommended, but not required, to follow
Maven's [guide to naming conventions](https://maven.apache.org/guides/mini/guide-naming-conventions.html).
"""


type ModId = Annotated[
    str,
    Field(pattern=f"^{MOD_ID_PATTERN}$"),
]
"""A unique identifier for the mod or library defined by this file.

Must match the `^[a-z][a-z0-9-_]{1,63}$` regular expression. Best practice is that mod
ID's are in snake_case.
"""


type ModIdWithGroup = Annotated[
    str,
    Field(pattern=f"^({MAVEN_GROUP_PATTERN}:)?{MOD_ID_PATTERN}$"),
]
"""A mod identifier in the form of either `mavenGroup:modId` or `modId`."""


class ProvidesObject(_QuiltModel):
    """Defines the identifier and optionally version range of another mod that this
    package provides.

    It can be represented as either an object containing at least the id field, or a
    string mod identifier in the form of either `mavenGroup:modId` or `modId`.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#provides-objects
    """

    id: ModIdWithGroup
    """A mod identifier in the form of either `mavenGroup:modId` or `modId`."""
    version: str = ""
    """Should be a valid mod version.

    If omitted, then this defaults to the version of the providing mod.
    """

    @model_validator(mode="before")
    @classmethod
    def _validate_str(cls, value: Any):
        if isinstance(value, str):
            return {"id": value}
        return value


class Entrypoint(_QuiltModel):
    """An object representing an entrypoint.

    If an entrypoint does not need to specify a language adapter other than the default
    language adapter, the entrypoint can be represented simply as the value string
    instead.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#the-entrypoints-field
    """

    adapter: str = "default"
    """Language adapter to use for this entrypoint.

    By default this is `default` and tells loader to parse using the JVM entrypoint
    notation.
    """
    value: str
    """Points to an implementation of the entrypoint."""

    @model_validator(mode="before")
    @classmethod
    def _validate_str(cls, value: Any):
        if isinstance(value, str):
            return {"value": value}
        return value


type VersionSpecifier = str
"""A version range specifier.

https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#string
"""


type VersionArray = list[VersionSpecifier]
"""An array of version specifiers defining the versions this dependency applies to.

The dependency matches if it matches ANY of the listed versions.

https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#array-deprecated
"""


class AnyVersion(_QuiltModel):
    """A dependency that matches if it matches ANY of the listed versions.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#object
    """

    any: list[VersionSpecifier | VersionObject]


class AllVersions(_QuiltModel):
    """A dependency that matches if it matches ALL of the listed versions.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#object
    """

    all: list[VersionSpecifier | VersionObject]


type VersionObject = AnyVersion | AllVersions
"""A version object containing a single field, which must either be `any` or `all`.

https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#object
"""


class DependencyObject(_QuiltModel):
    """A dependency object defines what mods/plugins a given mod depends on or breaks.

    It can be represented as either an object containing at least the id field, a string
    mod identifier in the form of either `mavenGroup:modId` or `modId`, or an array of
    dependency objects. If an array of dependency objects is provided, the dependency
    matches if it matches ANY of the dependency objects for the "depends" and "unless"
    fields, and ALL for the "breaks" field.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#dependency-objects
    """

    id: ModIdWithGroup
    """A mod identifier in the form of either `mavenGroup:modId` or `modId`."""
    versions: VersionSpecifier | VersionArray | VersionObject = "*"
    """A version specifier, or complex set of version specifiers that control what
    versions match this dependency object."""
    reason: str | None = None
    """A short, human-readable reason for the dependency object to exist."""
    optional: bool = False
    """Dependencies marked as `optional` will only be checked if the mod/plugin
    specified by the `id` field is present."""
    unless: DependencyObject | None = None
    """Describes situations where this dependency can be ignored."""

    @model_validator(mode="before")
    @classmethod
    def _validate_str(cls, value: Any):
        if isinstance(value, str):
            return {"id": value}
        return value


type Dependency = DependencyObject | list[DependencyObject]
"""A dependency object defines what mods/plugins a given mod depends on or breaks.

It can be represented as either an object containing at least the id field, a string
mod identifier in the form of either `mavenGroup:modId` or `modId`, or an array of
dependency objects. If an array of dependency objects is provided, the dependency
matches if it matches ANY of the dependency objects for the "depends" and "unless"
fields, and ALL for the "breaks" field.

https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#dependency-objects
"""


class LicenseObject(_QuiltModel):
    """A license object.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#the-license-field
    """

    name: str
    id: str
    url: str
    description: str | None = None


type License = str | LicenseObject
"""A license, defined as either an [SPDX identifier](https://spdx.org/licenses/) string
or a LicenseObject."""


class Metadata(_QuiltModel):
    """Optional metadata that can be used by mods to display information about the mods
    installed.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#the-metadata-field
    """

    name: str | None = None
    """A human-readable name for this mod."""
    description: str | None = None
    """A human-readable description of this mod.

    This description should be plain text, with the exception of line breaks, which can
    be represented with the newline character `\\n`.
    """
    contributors: dict[str, str | list[str]] = Field(default_factory=dict)
    """A collection of `key: value` pairs denoting the persons or organizations that
    contributed to this project.

    The key should be the name of the person or organization, while the value can be
    either a string representing a single role or an array of strings each one
    representing a single role.

    A role can be any valid string. The "Owner" role is defined as being the person(s)
    or organization in charge of the project.
    """
    contact: dict[str, str] = Field(default_factory=dict)
    """A collection of `key: value` pairs denoting various contact information for the
    people behind this mod, with all values being strings.

    The following keys are officially defined, though mods can provide as many
    additional values as they wish:

    * email — Valid e-mail address for the organization/developers.
    * homepage — Valid HTTP/HTTPS address for the project or the organization/developers
    behind it.
    * issues — Valid HTTP/HTTPS address for the project issue tracker.
    * sources — Valid HTTP/HTTPS address for a source code repository.
    """
    license: License | list[License] | None = None
    """The license or array of licenses this project operates under."""
    icon: Path | dict[str, Path] | None = None
    """One or more paths to a square .PNG file.

    If an object is provided, the keys must be the resolution of the corresponding file.
    """


class QuiltLoader(_QuiltModel):
    """Information necessary for the mod loading process.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#the-quilt_loader-field
    """

    group: MavenGroup
    """The Maven group id.

    A unique identifier for the organization behind or developers of the mod. The group
    string must match the `^[a-zA-Z0-9-_.]+$` regular expression, and must not begin
    with the reserved namespace `loader.plugin.` It is recommended, but not required, to
    follow Maven's [guide to naming conventions](https://maven.apache.org/guides/mini/guide-naming-conventions.html).
    """
    id: ModId
    """The mod id.

    A unique identifier for the mod or library defined by this file. Must match the
    `^[a-z][a-z0-9-_]{1,63}$` regular expression. Best practice is that mod ID's are in
    snake_case.
    """
    provides: list[ProvidesObject] = Field(default_factory=list)
    """Alternative mods provided by this mod.

    An array of `ProvidesObject`s describing other mods/APIs that this package provides.
    """
    version: str
    """The mod's version.

    Must conform to the Semantic Versioning 2.0.0 specification.
    """
    entrypoints: dict[str, Entrypoint | list[Entrypoint]] = Field(default_factory=dict)
    """A collection of `key: value` pairs, where each key is the type of the entrypoints
    specified and each value is either a single entrypoint or an array of
    entrypoints."""
    plugins: list[Entrypoint] = Field(default_factory=list)
    """An array of loader plugins.

    A plugin object follows the same schema as an entrypoint object, so the `Entrypoint`
    type is reused here.
    """
    jars: list[Path] = Field(default_factory=list)
    """Array of nested JARs to be loaded.

    A list of paths to nested JAR files to load, relative to the root directory inside
    of the mod's JAR.
    """
    language_adapters: dict[str, str] = Field(default_factory=dict)
    """Array of language adapters.

    A collection of `key: value` pairs, where each key is the namespace of a language
    adapter and the value is an implementation of the `LanguageAdapter` interface.
    """
    depends: list[Dependency] = Field(default_factory=list)
    """Collection of mod dependencies.

    Defines mods that this mod will not function without.
    """
    breaks: list[Dependency] = Field(default_factory=list)
    """Collection of mods that this mod is incompatible with.

    Defines mods that this mod either breaks or is broken by.
    """
    load_type: Literal["always", "if_possible", "if_required"] = "always"
    """How eagerly to load this mod.

    Influences whether or not a mod candidate should be loaded or not. May be any of
    these values:

    * "always" (default for mods directly in the mods folder)
    * "if_possible"
    * "if_required" (default for jar-in-jar mods)

    This doesn't affect mods directly placed in the mods folder.
    """
    repositories: list[HttpUrl] = Field(default_factory=list)
    """Array of maven repositories."""
    intermediate_mappings: str = Field(
        default="org.quiltmc:hashed",
        pattern=r"^[a-zA-Z0-9-_.]+:[a-zA-Z0-9-_.]+$",
    )
    """The intermediate mappings used for this mod.

    The intermediate mappings string must be a valid maven coordinate and match the
    `^[a-zA-Z0-9-_.]+:[a-zA-Z0-9-_.]+$` regular expression. This field currently only
    officially supports `org.quiltmc:hashed` and `net.fabricmc:intermediary`.
    """
    metadata: Metadata = Field(default_factory=Metadata)
    """Extra information about this mod and/or its authors."""

    @model_validator(mode="after")
    def _set_default_provides_versions(self):
        for provides in self.provides:
            if not provides.version:
                provides.version = self.version
        return self


type Environment = Literal["*", "client", "dedicated_server"]
"""A game environment that something should be loaded on.

Valid values are:

* `"*"` — All environments (default)
* `"client"` — The physical client
* `"dedicated_server"` — The dedicated server

https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#the-environment-field
"""


class Mixin(_QuiltModel):
    """A mixin config entry.

    Providing a string is the same as providing a mixin configuration entry with a
    config field and no environment field.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#the-mixin-field
    """

    config: Path
    """A path to the mixin config file relative to the root of the mod JAR."""
    environment: Environment = "*"
    """The environment in which the config should be loaded."""

    @model_validator(mode="before")
    @classmethod
    def _validate_str(cls, value: Any):
        if isinstance(value, str):
            return {"config": value}
        return value


class Minecraft(_QuiltModel):
    """Contains flags and options related to Minecraft specifically.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md#the-minecraft-field
    """

    environment: Environment = "*"


class QuiltMod(_QuiltModel):
    """A `quilt.mod.json` file.

    https://github.com/QuiltMC/rfcs/blob/bd9bb83/specification/0002-quilt.mod.json.md
    """

    schema_version: Literal[1]
    """The schemaVersion to be used for reading this file."""
    quilt_loader: QuiltLoader
    """Information related to loading the mod."""
    mixin: Mixin | list[Mixin] | None = None
    """Path(s) to mixin config file(s).

    A single or array of mixin configuration entries.
    """
    access_widener: Path | list[Path] | None = None
    """Path(s) to accesswidener file(s).

    A single or array of paths to access widener files relative to the root of the mod
    JAR.
    """
    minecraft: Minecraft = Field(default_factory=Minecraft)
    """Minecraft related options."""

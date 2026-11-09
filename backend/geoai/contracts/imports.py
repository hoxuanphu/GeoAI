"""Offline inspection records; policies come from trusted administrator config.

An inventory is metadata, never a native file grant, AssetRef or model approval.
"""
from typing import Annotated, Literal
import ipaddress
import re

from pydantic import Field, StringConstraints, model_validator

from .common import Contract, Identifier, NonNegativeInt, PositiveInt, Sha256, ValueModel

Extension = Annotated[str, StringConstraints(pattern=r"^\.[a-z0-9]{1,16}$")]


class ArchivePolicy(Contract):
    policy_id: Identifier
    max_archive_bytes: PositiveInt
    max_entries: PositiveInt
    max_total_bytes: PositiveInt
    max_entry_bytes: PositiveInt
    max_path_depth: PositiveInt
    max_compression_ratio: Annotated[float, Field(strict=True, gt=0)]
    max_seconds: Annotated[float, Field(strict=True, gt=0)]
    chunk_bytes: Annotated[int, Field(strict=True, gt=0, le=1048576)]
    allowed_extensions: Annotated[tuple[Extension, ...], Field(min_length=1)]
    nested_archives: Literal["reject"]

    @model_validator(mode="after")
    def unique_extensions(self):
        if len(set(self.allowed_extensions)) != len(self.allowed_extensions):
            raise ValueError("duplicate extension policy")
        return self


class ArchiveEntry(ValueModel):
    relative_path: Annotated[str, StringConstraints(min_length=1)]
    kind: Literal["file", "directory"]
    size_bytes: NonNegativeInt
    compressed_bytes: NonNegativeInt
    sha256: Sha256


class ArchiveInventory(Contract):
    inventory_id: Identifier
    policy_id: Identifier
    policy_sha256: Sha256
    archive_sha256: Sha256
    archive_bytes: NonNegativeInt
    entries: tuple[ArchiveEntry, ...]
    total_bytes: NonNegativeInt

    @model_validator(mode="after")
    def consistent_totals(self):
        if self.total_bytes != sum(item.size_bytes for item in self.entries):
            raise ValueError("inventory byte total mismatch")
        return self


class ProviderEndpoint(ValueModel):
    scheme: Literal["http", "https"]
    host: Annotated[str, StringConstraints(min_length=1, max_length=253)]
    port: Annotated[int, Field(strict=True, gt=0, le=65535)]

    @model_validator(mode="after")
    def canonical_host(self):
        try:
            address = ipaddress.ip_address(self.host)
            valid = self.host == address.compressed
        except ValueError:
            valid = (self.host == self.host.lower() and all(
                re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                for label in self.host.split(".")))
        if not valid:
            raise ValueError("endpoint requires canonical host")
        return self


class ProviderPolicy(Contract):
    policy_id: Identifier
    provider_id: Identifier
    endpoints: Annotated[tuple[ProviderEndpoint, ...], Field(min_length=1)]
    allowed_private_networks: tuple[str, ...]
    max_requests: PositiveInt
    max_redirects: NonNegativeInt
    max_bytes: PositiveInt
    max_seconds: Annotated[float, Field(strict=True, gt=0)]
    max_chunk_bytes: Annotated[int, Field(strict=True, gt=0, le=1048576)]
    max_address_records: PositiveInt
    max_url_length: PositiveInt

    @model_validator(mode="after")
    def explicit_private_profile(self):
        rfc1918 = tuple(ipaddress.ip_network(value) for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
        for value in self.allowed_private_networks:
            network = ipaddress.ip_network(value, strict=True)
            if network.version != 4 or not any(network.subnet_of(parent) for parent in rfc1918):
                raise ValueError("private profile is restricted to RFC1918 subnets")
        if len(set(self.endpoints)) != len(self.endpoints):
            raise ValueError("duplicate endpoint")
        return self


class ProviderAssetBinding(ValueModel):
    provider_id: Identifier
    asset_id: Identifier
    version_id: Identifier

    @model_validator(mode="after")
    def provider_namespace(self):
        if not self.asset_id.startswith(self.provider_id + ":"):
            raise ValueError("asset requires provider namespace")
        return self


class ProviderRequestPlan(ValueModel):
    binding: ProviderAssetBinding
    origin: tuple[str, str, int]
    # Do not include this private return value in log/snapshot: headers may be secret.
    headers: tuple[tuple[str, str], ...] = Field(repr=False, exclude=True)


class ProviderStreamReceipt(ValueModel):
    binding: ProviderAssetBinding
    size_bytes: NonNegativeInt
    sha256: Sha256

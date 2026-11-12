"""Private Linux owner journal metadata; never a substitute for native evidence."""
import json
from pathlib import PurePosixPath
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints, field_validator, model_validator
from .access import FileIdentity
from .common import Contract, Identifier, PositiveInt, ValueModel

MAX_LEDGER_BYTES = 1048576


class LedgerCodecError(ValueError):
    """Sanitized journal rejection; callers must keep ownership fail closed."""


class LinuxOwnerGeneration(ValueModel):
    project_id: Identifier
    owner_id: Identifier
    owner_epoch: PositiveInt
    project_root_identity: FileIdentity
    boot_id: UUID
    invocation_id: Annotated[str, StringConstraints(min_length=32,max_length=32,pattern=r'^[0-9a-f]{32}$')]
    supervisor_pid: PositiveInt
    supervisor_start_ticks: PositiveInt
    cgroup_path: Annotated[str, StringConstraints(min_length=1,max_length=4096)]
    cgroup_identity: FileIdentity
    state: Literal['active','closed']

    @field_validator('cgroup_path')
    @classmethod
    def canonical_cgroup_path(cls,value):
        path=PurePosixPath(value)
        if (not path.is_absolute() or value.startswith('//') or str(path) != value
                or '..' in path.parts or any(ord(c)<32 or ord(c)==127 for c in value)
                or path.name != 'geoai-execution.service'):
            raise ValueError('invalid_cgroup_path')
        # Syntax only: the native observer still verifies UID, invocation, FD and
        # actual user-manager cgroup identity. No OS probe belongs in contracts.
        return value


class LinuxOwnerLedger(Contract):
    epoch_high_watermark: PositiveInt
    generations: Annotated[tuple[LinuxOwnerGeneration,...],Field(min_length=1,max_length=1024)]

    @model_validator(mode='after')
    def unique_generations(self):
        if (len({g.owner_id for g in self.generations}) != len(self.generations)
                or len({g.owner_epoch for g in self.generations}) != len(self.generations)
                or self.epoch_high_watermark < max(g.owner_epoch for g in self.generations)):
            raise ValueError('invalid_generation_history')
        return self


def _object_pairs(pairs):
    value={}
    for key,item in pairs:
        if key in value: raise LedgerCodecError('duplicate_json_key')
        value[key]=item
    return value


def _invalid_constant(value):
    raise LedgerCodecError('invalid_json_number')


def decode_ledger(data: bytes) -> LinuxOwnerLedger:
    if type(data) is not bytes:
        raise LedgerCodecError('invalid_owner_ledger')
    if len(data)>MAX_LEDGER_BYTES:
        raise LedgerCodecError('owner_ledger_too_large')
    if not data.endswith(b'}\n'):
        raise LedgerCodecError('invalid_owner_ledger_frame')
    try:
        payload=json.loads(data[:-1].decode('utf-8'),object_pairs_hook=_object_pairs,
                           parse_constant=_invalid_constant)
        return LinuxOwnerLedger.model_validate(payload)
    except (ValueError,TypeError,RecursionError):
        raise LedgerCodecError('invalid_owner_ledger') from None


def encode_ledger(value: LinuxOwnerLedger) -> bytes:
    if type(value) is not LinuxOwnerLedger:
        raise LedgerCodecError('invalid_owner_ledger')
    try:
        # Revalidate even if a trusted caller accidentally used model_construct.
        checked=LinuxOwnerLedger.model_validate(value.model_dump(mode='python',warnings='error'))
        data=json.dumps(checked.model_dump(mode='json'),ensure_ascii=False,
                        allow_nan=False,separators=(',',':')).encode('utf-8')+b'\n'
    except (ValueError,TypeError,RecursionError):
        raise LedgerCodecError('invalid_owner_ledger') from None
    if len(data)>MAX_LEDGER_BYTES:
        raise LedgerCodecError('owner_ledger_too_large')
    return data

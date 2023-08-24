from dataclasses import dataclass, field

from models.common import Position


@dataclass(frozen=True)
class DotlanConnectionEndpoint:
    sys_id: int
    Position: Position


@dataclass(frozen=True)
class DotlanConnection:
    connection_type: str
    origin: DotlanConnectionEndpoint
    destination: DotlanConnectionEndpoint


@dataclass(frozen=True)
class DotlanSystem:
    sys_id: int
    name: str
    Position: Position
    has_ice: bool = field(kw_only=True, default=True)
    faction: str = field(kw_only=True, default="")
    has_refinery: bool = field(kw_only=True, default=True)
    has_factory: bool = field(kw_only=True, default=True)
    has_research: bool = field(kw_only=True, default=True)
    has_cloning: bool = field(kw_only=True, default=True)


@dataclass(frozen=True)
class DotlanRegionOffset:
    center_x: float
    center_y: float
    offset_x: float
    offset_y: float

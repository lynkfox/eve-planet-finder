from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

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


@dataclass
class DotlanSystem:
    System_Id: int
    Name: str
    Position: Position
    has_ice: bool = field(kw_only=True, default=False)
    faction: str = field(kw_only=True, default="")
    has_refinery: bool = field(kw_only=True, default=False)
    has_industry: bool = field(kw_only=True, default=False)
    has_research: bool = field(kw_only=True, default=False)
    has_cloning: bool = field(kw_only=True, default=False)
    dotlan_link: str = field(kw_only=True, default="")
    More: DotlanAdditionalSystemData = field(init=False, default=None)

    def __getstate__(self):
        return (
            self.System_Id,
            self.Name,
            self.has_ice,
            self.faction,
            self.has_refinery,
            self.has_industry,
            self.has_research,
            self.has_cloning,
            self.dotlan_link,
            self.More,
        )

    def __setstate__(self, state):
        (
            self.System_Id,
            self.Name,
            self.has_ice,
            self.faction,
            self.has_refinery,
            self.has_industry,
            self.has_research,
            self.has_cloning,
            self.dotlan_link,
            self.More,
        ) = state


@dataclass(frozen=True)
class DotlanRegionOffset:
    center_x: float
    center_y: float
    offset_x: float
    offset_y: float


@dataclass(frozen=True)
class DotlanAgent:
    Name: str
    Station: str
    System_Id: int
    Corporation: str
    Level: int
    Notes: str

    def __getstate__(self):
        return (self.Name, self.Station, self.System_Id, self.Corporation, self.Level, self.Notes)

    def __setstate__(self, state):
        (self.Name, self.Station, self.System_Id, self.Corporation, self.Level, self.Notes) = state


@dataclass(frozen=True)
class DotlanStation:
    Name: str
    FactionImage: str
    Corporation: str
    Services: List[str]
    Type: str
    System_Id: int = field(kw_only=True, default=0)

    def __getstate__(self):
        return (self.Name, self.FactionImage, self.Corporation, self.Services, self.Type, self.System_Id)

    def __setstate__(self, state):
        (self.Name, self.FactionImage, self.Corporation, self.Services, self.Type, self.System_Id) = state


@dataclass
class DotlanAdditionalSystemData:
    Planets: int
    Moons: int
    Belts: int
    SecurityClass: str
    PirateFaction: str
    Stations: List[DotlanStation] = field(init=False, default_factory=list)
    Agents: List[DotlanAgent] = field(init=False, default_factory=list)

    def __getstate__(self):
        return (
            self.Planets,
            self.Moons,
            self.Belts,
            self.SecurityClass,
            self.PirateFaction,
            self.Stations,
            self.Agents,
        )

    def __setstate__(self, state):
        (
            self.Planets,
            self.Moons,
            self.Belts,
            self.SecurityClass,
            self.PirateFaction,
            self.Stations,
            self.Agents,
        ) = state

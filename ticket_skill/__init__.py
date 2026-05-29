"""Ticket grabbing demo skill for Dragon Boat Festival high-speed rail trips."""

__all__ = [
    "DemoRailwayProvider",
    "Passenger",
    "TicketGrabRequest",
    "TicketGrabResult",
    "TicketGrabber",
]


def __getattr__(name: str):
    if name in __all__:
        from . import skill

        return getattr(skill, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

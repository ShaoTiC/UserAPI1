"""A safe, local 12306-style high-speed rail ticket grabbing skill.

This module models the workflow a traveler needs when trying to grab a ticket:
choose a route, choose a train, choose a seat class, and receive a success or
failure result that can be rendered by a web page.  It intentionally uses a demo
provider instead of automating the real 12306 website, so it does not bypass
CAPTCHA, queueing, identity verification, payment, or any official controls.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Iterable


SEAT_TYPES: dict[str, str] = {
    "first_class": "一等座",
    "second_class": "二等座",
    "standing": "无座",
}


STATIONS: tuple[str, ...] = (
    "北京南",
    "上海虹桥",
    "广州南",
    "深圳北",
    "杭州东",
    "南京南",
    "武汉",
    "长沙南",
    "成都东",
    "西安北",
)


@dataclass(frozen=True)
class Passenger:
    """Passenger information required to create an order result."""

    name: str
    id_number: str = ""
    phone: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Passenger":
        return cls(
            name=str(data.get("name", "")).strip(),
            id_number=str(data.get("id_number", "")).strip(),
            phone=str(data.get("phone", "")).strip(),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name:
            errors.append("请填写购买人姓名")
        return errors


@dataclass(frozen=True)
class TrainOption:
    """A selectable train for a route and date."""

    train_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    gate: str
    seat_inventory: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "train_number": self.train_number,
            "origin": self.origin,
            "destination": self.destination,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "gate": self.gate,
            "seat_inventory": copy.deepcopy(self.seat_inventory),
            "seat_labels": SEAT_TYPES,
        }


@dataclass(frozen=True)
class TicketGrabRequest:
    """User choices for one ticket grabbing attempt."""

    passenger: Passenger
    travel_date: str
    origin: str
    destination: str
    seat_types: list[str] = field(default_factory=lambda: ["second_class"])
    train_number: str | None = None
    max_attempts: int = 5
    wait_seconds: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TicketGrabRequest":
        passenger_data = data.get("passenger") or {}
        if isinstance(passenger_data, str):
            passenger_data = {"name": passenger_data}

        seat_types = data.get("seat_types") or data.get("seat_type") or ["second_class"]
        if isinstance(seat_types, str):
            seat_types = [seat_types]

        return cls(
            passenger=Passenger.from_dict(passenger_data),
            travel_date=str(data.get("travel_date", "")).strip(),
            origin=str(data.get("origin", "")).strip(),
            destination=str(data.get("destination", "")).strip(),
            seat_types=[str(seat_type).strip() for seat_type in seat_types],
            train_number=(
                str(data.get("train_number", "")).strip()
                if data.get("train_number")
                else None
            ),
            max_attempts=int(data.get("max_attempts") or 5),
            wait_seconds=float(data.get("wait_seconds") or 0.0),
        )

    def validate(self) -> list[str]:
        errors = self.passenger.validate()

        if not self.origin:
            errors.append("请选择起始地")
        elif self.origin not in STATIONS:
            errors.append(f"暂不支持起始地：{self.origin}")

        if not self.destination:
            errors.append("请选择终止地")
        elif self.destination not in STATIONS:
            errors.append(f"暂不支持终止地：{self.destination}")

        if self.origin and self.destination and self.origin == self.destination:
            errors.append("起始地和终止地不能相同")

        try:
            datetime.strptime(self.travel_date, "%Y-%m-%d")
        except ValueError:
            errors.append("乘车日期必须为 YYYY-MM-DD")

        if not self.seat_types:
            errors.append("请选择至少一种席别")
        else:
            invalid_seats = [seat for seat in self.seat_types if seat not in SEAT_TYPES]
            if invalid_seats:
                errors.append(f"不支持的席别：{', '.join(invalid_seats)}")

        if self.max_attempts < 1:
            errors.append("最大抢票次数不能小于 1")
        if self.wait_seconds < 0:
            errors.append("抢票间隔不能为负数")

        return errors


@dataclass(frozen=True)
class TicketGrabResult:
    """Result payload returned to the API layer and front-end page."""

    success: bool
    message: str
    attempts: int
    order: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "attempts": self.attempts,
            "order": copy.deepcopy(self.order),
            "failure": copy.deepcopy(self.failure),
        }


class DemoRailwayProvider:
    """Deterministic in-memory provider for selectable stations and trains."""

    def __init__(self) -> None:
        self._inventory: dict[tuple[str, str, str, str, str], int] = {}

    def stations(self) -> list[str]:
        return list(STATIONS)

    def trains(self, origin: str, destination: str, travel_date: str) -> list[TrainOption]:
        if origin == destination or origin not in STATIONS or destination not in STATIONS:
            return []

        trip_date = _parse_date_or_today(travel_date)
        route_seed = _stable_int(f"{origin}:{destination}:{trip_date.isoformat()}")
        route_rng = random.Random(route_seed)
        train_count = 4
        trains: list[TrainOption] = []

        for index in range(train_count):
            depart_hour = 7 + index * 3 + route_rng.randint(0, 1)
            depart_minute = route_rng.choice([0, 12, 26, 38, 52])
            depart = datetime.combine(trip_date, datetime.min.time()) + timedelta(
                hours=depart_hour,
                minutes=depart_minute,
            )
            duration = timedelta(hours=3 + route_rng.randint(0, 4), minutes=route_rng.choice([18, 35, 48]))
            arrive = depart + duration
            train_number = f"G{200 + (route_seed + index * 137) % 7000}"
            gate = f"{route_rng.choice('ABCDEF')}{route_rng.randint(1, 18):02d}"
            seat_inventory = {
                seat_type: self._current_inventory(
                    travel_date=trip_date.isoformat(),
                    origin=origin,
                    destination=destination,
                    train_number=train_number,
                    seat_type=seat_type,
                )
                for seat_type in SEAT_TYPES
            }
            trains.append(
                TrainOption(
                    train_number=train_number,
                    origin=origin,
                    destination=destination,
                    departure_time=depart.strftime("%Y-%m-%d %H:%M"),
                    arrival_time=arrive.strftime("%Y-%m-%d %H:%M"),
                    gate=gate,
                    seat_inventory=seat_inventory,
                )
            )

        return trains

    def reserve(self, request: TicketGrabRequest) -> tuple[TrainOption | None, str | None]:
        candidates = self.trains(request.origin, request.destination, request.travel_date)
        if request.train_number:
            candidates = [
                train
                for train in candidates
                if train.train_number == request.train_number
            ]

        for train in candidates:
            for seat_type in request.seat_types:
                key = self._inventory_key(
                    request.travel_date,
                    request.origin,
                    request.destination,
                    train.train_number,
                    seat_type,
                )
                if self._inventory[key] > 0:
                    self._inventory[key] -= 1
                    updated_inventory = dict(train.seat_inventory)
                    updated_inventory[seat_type] = self._inventory[key]
                    return (
                        TrainOption(
                            train_number=train.train_number,
                            origin=train.origin,
                            destination=train.destination,
                            departure_time=train.departure_time,
                            arrival_time=train.arrival_time,
                            gate=train.gate,
                            seat_inventory=updated_inventory,
                        ),
                        seat_type,
                    )

        return None, None

    def _current_inventory(
        self,
        *,
        travel_date: str,
        origin: str,
        destination: str,
        train_number: str,
        seat_type: str,
    ) -> int:
        key = self._inventory_key(travel_date, origin, destination, train_number, seat_type)
        if key not in self._inventory:
            self._inventory[key] = _initial_inventory(key)
        return self._inventory[key]

    @staticmethod
    def _inventory_key(
        travel_date: str,
        origin: str,
        destination: str,
        train_number: str,
        seat_type: str,
    ) -> tuple[str, str, str, str, str]:
        return (travel_date, origin, destination, train_number, seat_type)


class TicketGrabber:
    """Runs repeated ticket-grabbing attempts against a railway provider."""

    def __init__(self, provider: DemoRailwayProvider | None = None) -> None:
        self.provider = provider or DemoRailwayProvider()

    def stations(self) -> list[str]:
        return self.provider.stations()

    def trains(self, origin: str, destination: str, travel_date: str) -> list[dict[str, Any]]:
        return [
            train.to_dict()
            for train in self.provider.trains(origin, destination, travel_date)
        ]

    def grab(self, request: TicketGrabRequest) -> TicketGrabResult:
        errors = request.validate()
        if errors:
            return TicketGrabResult(
                success=False,
                message="请求参数不完整",
                attempts=0,
                failure={
                    "reason": "参数校验失败",
                    "details": errors,
                    "request": _request_summary(request),
                },
            )

        for attempt in range(1, request.max_attempts + 1):
            train, seat_type = self.provider.reserve(request)
            if train and seat_type:
                return TicketGrabResult(
                    success=True,
                    message="购买成功",
                    attempts=attempt,
                    order=_build_order(request, train, seat_type),
                )
            if request.wait_seconds and attempt < request.max_attempts:
                time.sleep(request.wait_seconds)

        return TicketGrabResult(
            success=False,
            message="购买失败",
            attempts=request.max_attempts,
            failure={
                "reason": "所选车次和席别暂无余票",
                "request": _request_summary(request),
                "available_trains": self.trains(
                    request.origin,
                    request.destination,
                    request.travel_date,
                ),
            },
        )


def _build_order(
    request: TicketGrabRequest,
    train: TrainOption,
    seat_type: str,
) -> dict[str, Any]:
    return {
        "order_id": f"MOCK-{uuid.uuid4().hex[:12].upper()}",
        "buyer": request.passenger.name,
        "passenger": {
            "name": request.passenger.name,
            "id_number": _mask_id_number(request.passenger.id_number),
            "phone": _mask_phone(request.passenger.phone),
        },
        "travel_date": request.travel_date,
        "departure_time": train.departure_time,
        "arrival_time": train.arrival_time,
        "origin": train.origin,
        "destination": train.destination,
        "gate": train.gate,
        "seat_number": _seat_number(seat_type),
        "seat_type": seat_type,
        "seat_type_label": SEAT_TYPES[seat_type],
        "train_number": train.train_number,
        "paid": False,
        "payment_notice": "演示订单未发起真实支付，请以 12306 官方订单为准",
    }


def _request_summary(request: TicketGrabRequest) -> dict[str, Any]:
    return {
        "buyer": request.passenger.name,
        "travel_date": request.travel_date,
        "origin": request.origin,
        "destination": request.destination,
        "train_number": request.train_number,
        "seat_types": [
            {"value": seat_type, "label": SEAT_TYPES.get(seat_type, seat_type)}
            for seat_type in request.seat_types
        ],
    }


def _initial_inventory(key: tuple[str, str, str, str, str]) -> int:
    seat_type = key[-1]
    number = _stable_int(":".join(key))
    if seat_type == "first_class":
        return number % 2
    if seat_type == "second_class":
        return number % 4
    return number % 6


def _seat_number(seat_type: str) -> str:
    carriage = random.randint(1, 16)
    row = random.randint(1, 18)
    suffixes = {
        "first_class": ["A", "C", "F"],
        "second_class": ["A", "B", "C", "D", "F"],
        "standing": ["无座"],
    }
    suffix = random.choice(suffixes[seat_type])
    if seat_type == "standing":
        return f"{carriage:02d}车{suffix}"
    return f"{carriage:02d}车{row:02d}{suffix}"


def _stable_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def _parse_date_or_today(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return date.today()


def _mask_id_number(value: str) -> str:
    if len(value) < 8:
        return value
    return f"{value[:3]}********{value[-4:]}"


def _mask_phone(value: str) -> str:
    if len(value) != 11:
        return value
    return f"{value[:3]}****{value[-4:]}"


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local 12306-style ticket grabbing demo.")
    parser.add_argument("--passenger", required=True, help="购买人姓名")
    parser.add_argument("--origin", required=True, help="起始地")
    parser.add_argument("--destination", required=True, help="终止地")
    parser.add_argument("--travel-date", required=True, help="乘车日期，格式 YYYY-MM-DD")
    parser.add_argument("--train-number", help="指定车次，例如 G1234")
    parser.add_argument(
        "--seat-type",
        action="append",
        choices=sorted(SEAT_TYPES),
        default=None,
        help="席别，可重复传入：first_class、second_class、standing",
    )
    parser.add_argument("--max-attempts", type=int, default=5, help="最大抢票次数")
    args = parser.parse_args(list(argv) if argv is not None else None)

    request = TicketGrabRequest(
        passenger=Passenger(name=args.passenger),
        travel_date=args.travel_date,
        origin=args.origin,
        destination=args.destination,
        train_number=args.train_number,
        seat_types=args.seat_type or ["second_class"],
        max_attempts=args.max_attempts,
    )
    result = TicketGrabber().grab(request)
    print(json.dumps(result, ensure_ascii=False, default=_json_default, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())

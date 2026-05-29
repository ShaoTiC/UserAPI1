import unittest

from ticket_skill.skill import (
    DemoRailwayProvider,
    Passenger,
    STATIONS,
    TicketGrabRequest,
    TicketGrabber,
)


class TicketSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = DemoRailwayProvider()
        self.grabber = TicketGrabber(self.provider)
        self.travel_date = "2026-06-19"

    def test_lists_stations_and_trains(self) -> None:
        stations = self.grabber.stations()
        self.assertIn("北京南", stations)

        trains = self.grabber.trains("北京南", "上海虹桥", self.travel_date)
        self.assertGreater(len(trains), 0)
        self.assertEqual(trains[0]["origin"], "北京南")
        self.assertEqual(trains[0]["destination"], "上海虹桥")
        self.assertIn("seat_inventory", trains[0])

    def test_success_result_contains_purchase_page_fields(self) -> None:
        train, seat_type = self._find_available_train()
        request = TicketGrabRequest(
            passenger=Passenger(name="张三", id_number="110101199001011234", phone="13800138000"),
            travel_date=self.travel_date,
            origin=train["origin"],
            destination=train["destination"],
            train_number=train["train_number"],
            seat_types=[seat_type],
        )

        result = self.grabber.grab(request)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.order)
        order = result.order or {}
        for field in (
            "buyer",
            "departure_time",
            "origin",
            "destination",
            "gate",
            "seat_number",
            "train_number",
            "seat_type_label",
        ):
            self.assertIn(field, order)
        self.assertEqual(order["buyer"], "张三")
        self.assertEqual(order["train_number"], train["train_number"])

    def test_failure_when_requested_train_has_no_remaining_inventory(self) -> None:
        train = self.grabber.trains("北京南", "上海虹桥", self.travel_date)[0]
        seat_types = ["first_class", "second_class", "standing"]
        total_inventory = sum(train["seat_inventory"][seat] for seat in seat_types)
        request = TicketGrabRequest(
            passenger=Passenger(name="李四"),
            travel_date=self.travel_date,
            origin="北京南",
            destination="上海虹桥",
            train_number=train["train_number"],
            seat_types=seat_types,
        )

        for _ in range(total_inventory):
            self.grabber.grab(request)
        result = self.grabber.grab(request)

        self.assertFalse(result.success)
        self.assertEqual(result.message, "购买失败")
        self.assertIsNotNone(result.failure)
        self.assertEqual(result.failure["reason"], "所选车次和席别暂无余票")

    def test_validation_failure_is_returned_as_failed_result(self) -> None:
        request = TicketGrabRequest(
            passenger=Passenger(name=""),
            travel_date="bad-date",
            origin="北京南",
            destination="北京南",
            seat_types=["vip"],
        )

        result = self.grabber.grab(request)

        self.assertFalse(result.success)
        self.assertEqual(result.attempts, 0)
        self.assertIn("参数校验失败", result.failure["reason"])

    def _find_available_train(self) -> tuple[dict, str]:
        for origin in STATIONS:
            for destination in STATIONS:
                if origin == destination:
                    continue
                for train in self.grabber.trains(origin, destination, self.travel_date):
                    for seat_type, count in train["seat_inventory"].items():
                        if count > 0:
                            return train, seat_type
        self.fail("Expected demo provider to expose at least one available seat")


if __name__ == "__main__":
    unittest.main()

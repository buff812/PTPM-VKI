import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from controller import Controller
from database import TriangleDatabase
from external_service import EmailService, ExternalService
from triangle_calculator import TriangleCalculator
from user_interface import ConsoleUserInterface, UserInterface


def make_controller(sides, database=None, calculator=None):
    user_interface = Mock(spec=UserInterface)
    user_interface.get_sides.return_value = sides
    external_service = Mock(spec=ExternalService)
    controller = Controller(
        calculator or TriangleCalculator(),
        database or TriangleDatabase(),
        user_interface,
        external_service,
    )
    return controller, external_service


class ControllerIntegrationTests(unittest.TestCase):
    def test_new_data_is_calculated_saved_and_sent(self):
        database = TriangleDatabase()
        controller, service = make_controller((3.0, 3.0, 3.0), database)
        result = controller.run()
        self.assertEqual(result, "равносторонний")
        self.assertEqual(database.get(3.0, 3.0, 3.0), ("равносторонний", None))
        service.send.assert_called_once_with(
            "Стороны: 3.0, 3.0, 3.0. Результат: равносторонний"
        )

    def test_existing_record_is_taken_from_database(self):
        database = TriangleDatabase()
        database.add(3.0, 4.0, 5.0, "из базы", None)
        calculator = Mock(spec=TriangleCalculator)
        controller, service = make_controller((3.0, 4.0, 5.0), database, calculator)
        result = controller.run()
        self.assertEqual(result, "из базы")
        calculator.get_triangle_type.assert_not_called()
        service.send.assert_called_once()

    def test_error_result_is_saved_and_returned(self):
        database = TriangleDatabase()
        controller, service = make_controller((1.0, 2.0, 10.0), database)
        result = controller.run()
        self.assertEqual(result, "Треугольник не существует")
        self.assertEqual(
            database.get(1.0, 2.0, 10.0), (None, "Треугольник не существует")
        )
        service.send.assert_called_once_with(
            "Стороны: 1.0, 2.0, 10.0. Результат: Треугольник не существует"
        )

    def test_second_run_with_same_data_uses_cache(self):
        database = TriangleDatabase()
        calculator = Mock(wraps=TriangleCalculator())
        controller, _ = make_controller((2.0, 2.0, 3.0), database, calculator)
        first = controller.run()
        second = controller.run()
        self.assertEqual(first, second)
        calculator.get_triangle_type.assert_called_once()

    @patch("builtins.input", side_effect=["5", "5", "8"])
    @patch("builtins.print")
    def test_full_chain_with_input_and_email_stubs(self, mocked_print, mocked_input):
        controller = Controller(
            TriangleCalculator(),
            TriangleDatabase(),
            ConsoleUserInterface(),
            EmailService(),
        )
        result = controller.run()
        self.assertEqual(result, "равнобедренный")
        self.assertEqual(mocked_input.call_count, 3)
        mocked_print.assert_called_once_with(
            "[EMAIL] Отправлено: Стороны: 5.0, 5.0, 8.0. Результат: равнобедренный"
        )


class CalculatorTests(unittest.TestCase):
    def test_all_branches(self):
        calculator = TriangleCalculator()
        self.assertEqual(
            calculator.get_triangle_type(0, 1, 1),
            (None, "Стороны должны быть положительными"),
        )
        self.assertEqual(calculator.get_triangle_type(3, 4, 5)[0], "разносторонний")
        self.assertEqual(calculator.get_triangle_type(2, 2, 3)[0], "равнобедренный")
        self.assertEqual(
            calculator.get_triangle_type(1, 1, 5),
            (None, "Треугольник не существует"),
        )


class DatabaseTests(unittest.TestCase):
    def test_add_get_delete(self):
        database = TriangleDatabase()
        self.assertIsNone(database.get(1, 2, 3))
        database.add(1, 2, 3, "тип", None)
        self.assertEqual(database.get(1, 2, 3), ("тип", None))
        self.assertTrue(database.delete(1, 2, 3))
        self.assertFalse(database.delete(1, 2, 3))
        self.assertIsNone(database.get(1, 2, 3))
        database.close()


class UserInterfaceAndMainTests(unittest.TestCase):
    @patch("builtins.input", side_effect=["abc"])
    def test_invalid_input_raises(self, _):
        with self.assertRaises(ValueError):
            ConsoleUserInterface().get_sides()

    def test_abstract_classes_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            UserInterface()
        with self.assertRaises(TypeError):
            ExternalService()
        self.assertIsNone(UserInterface.get_sides(None))
        self.assertIsNone(ExternalService.send(None, "x"))

    @patch("main.TriangleDatabase")
    @patch("main.EmailService")
    @patch("main.ConsoleUserInterface")
    @patch("main.print")
    def test_main_prints_controller_result(self, mocked_print, ui, email, db):
        ui.return_value.get_sides.return_value = (3.0, 4.0, 5.0)
        db.return_value.get.return_value = None
        main.main()
        mocked_print.assert_called_once_with("разносторонний")
        db.return_value.close.assert_called_once()


class MainGuardTest(unittest.TestCase):
    @patch("builtins.input", side_effect=["3", "3", "3"])
    @patch("builtins.print")
    def test_run_as_script(self, _, __):
        import runpy
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            cwd = os.getcwd()
            os.chdir(directory)
            try:
                runpy.run_module("main", run_name="__main__")
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()

from controller import Controller
from database import TriangleDatabase
from external_service import EmailService
from triangle_calculator import TriangleCalculator
from user_interface import ConsoleUserInterface


def main():
    database = TriangleDatabase("triangles.db")
    try:
        controller = Controller(
            TriangleCalculator(),
            database,
            ConsoleUserInterface(),
            EmailService(),
        )
        print(controller.run())
    finally:
        database.close()


if __name__ == "__main__":
    main()

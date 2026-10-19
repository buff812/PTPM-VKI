from abc import ABC, abstractmethod


class UserInterface(ABC):
    @abstractmethod
    def get_sides(self):
        pass


class ConsoleUserInterface(UserInterface):
    def get_sides(self):
        a = float(input("Введите длину первой стороны: "))
        b = float(input("Введите длину второй стороны: "))
        c = float(input("Введите длину третьей стороны: "))
        return a, b, c

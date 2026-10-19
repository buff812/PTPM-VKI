class Controller:
    def __init__(self, calculator, database, user_interface, external_service):
        self._calculator = calculator
        self._database = database
        self._user_interface = user_interface
        self._external_service = external_service

    def run(self):
        a, b, c = self._user_interface.get_sides()
        record = self._database.get(a, b, c)
        if record is None:
            triangle_type, error = self._calculator.get_triangle_type(a, b, c)
            self._database.add(a, b, c, triangle_type, error)
        else:
            triangle_type, error = record
        result = error if error else triangle_type
        message = f"Стороны: {a}, {b}, {c}. Результат: {result}"
        self._external_service.send(message)
        return result

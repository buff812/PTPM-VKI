class TriangleCalculator:
    def get_triangle_type(self, a, b, c):
        if a <= 0 or b <= 0 or c <= 0:
            return None, "Стороны должны быть положительными"
        if a + b <= c or a + c <= b or b + c <= a:
            return None, "Треугольник не существует"
        if a == b == c:
            return "равносторонний", None
        if a == b or b == c or a == c:
            return "равнобедренный", None
        return "разносторонний", None

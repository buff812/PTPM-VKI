from abc import ABC, abstractmethod


class ExternalService(ABC):
    @abstractmethod
    def send(self, message):
        pass


class EmailService(ExternalService):
    def send(self, message):
        print(f"[EMAIL] Отправлено: {message}")
        return True

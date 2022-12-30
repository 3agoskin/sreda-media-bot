from dataclasses import dataclass


@dataclass(frozen=True)
class Messages:
    test: str = "Привет {name}. Работаю..."


msg = Messages()

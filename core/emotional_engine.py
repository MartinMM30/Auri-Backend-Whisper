import datetime

class Actions:
    """
    Acciones que Auri puede ejecutar desde el backend.
    """

    @staticmethod
    def create_reminder(text: str):
        """
        Detecta fecha/hora simple y devuelve payload para Flutter.
        """
        now = datetime.datetime.now()

        return {
            "type": "action_create_reminder",
            "title": text,
            "date": now.isoformat(),
        }

    @staticmethod
    def get_weather_context(user_city: str):
        return {
            "city": user_city,
            "context": f"El clima en {user_city} es procesado desde Flutter.",
        }

    @staticmethod
    def get_user_profile(survey):
        return {
            "name": survey.get("userName", "Usuario"),
            "city": survey.get("userCity", ""),
        }

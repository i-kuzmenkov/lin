from interpreter import interpreter

# 1. Настройка модели (можно использовать OpenAI, Claude или локальную через Ollama)
interpreter.offline = False  # Поменяйте на True, если запускаете локально
interpreter.llm.model = "gpt-4o"  # Или, например, "ollama/deepseek-coder"

# 2. Прямая команда агенту на написание кода и работу с системой
interpreter.chat("Создай скрипт на Python, который скачивает погоду в Минске и сохраняет её в файл weather.txt")

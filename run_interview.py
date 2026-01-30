# !/usr/bin/env python3

import sys
import json
from main import interview_coach
from colorama import init, Fore, Style

init(autoreset=True)


def run_interactive_mode():
    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "MULTI-AGENT INTERVIEW COACH SYSTEM")
    print(Fore.CYAN + "=" * 60)

    from main import interview_coach
    interview_coach.reset()

    print(Fore.YELLOW + "\nВведите информацию о кандидате:")
    participant_name = input(Fore.GREEN + "Имя кандидата: ").strip()
    position = input(Fore.GREEN + "Позиция (например, Backend Developer): ").strip()
    grade = input(Fore.GREEN + "Грейд (Junior/Middle/Senior): ").strip()
    experience = input(Fore.GREEN + "Опыт: ").strip()

    print(Fore.CYAN + "\n" + "=" * 60)
    print(Fore.CYAN + "НАЧАЛО ИНТЕРВЬЮ")
    print(Fore.CYAN + "=" * 60)

    try:
        first_question = interview_coach.start_interview(
            participant_name, position, grade, experience
        )

        print(Fore.BLUE + "\n[Интервьюер]: " + Style.RESET_ALL + first_question)

        while True:
            print(Fore.YELLOW + "\n" + "-" * 40)
            user_input = input(Fore.GREEN + "Ваш ответ (или 'стоп интервью' для завершения): ").strip()

            if not user_input:
                print(Fore.RED + "Пожалуйста, введите ответ")
                continue

            response, internal_thoughts, is_end = interview_coach.process_response(user_input)

            if internal_thoughts:
                print(Fore.MAGENTA + "\n[Внутренние мысли агентов]:")
                for thought in internal_thoughts.split('\n'):
                    if thought.strip():
                        print(Fore.WHITE + "  " + thought)

            if is_end:
                print(Fore.CYAN + "\n" + "=" * 60)
                print(Fore.CYAN + "ИНТЕРВЬЮ ЗАВЕРШЕНО")
                print(Fore.CYAN + "=" * 60)
                print(Fore.GREEN + "\n" + response)
                break
            else:
                print(Fore.BLUE + "\n[Интервьюер]: " + Style.RESET_ALL + response)

    except Exception as e:
        print(Fore.RED + f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()


def run_scenario_mode(scenario_file: str):
    try:
        with open(scenario_file, 'r', encoding='utf-8') as f:
            scenario = json.load(f)
    except FileNotFoundError:
        print(Fore.RED + f"Файл сценария не найден: {scenario_file}")
        return
    except json.JSONDecodeError:
        print(Fore.RED + "Ошибка чтения JSON файла")
        return

    participant_name = scenario.get("participant_name", "Кандидат")
    position = scenario.get("position", "Developer")
    grade = scenario.get("grade", "Junior")
    experience = scenario.get("experience", "")
    user_responses = scenario.get("user_responses", [])

    print(Fore.CYAN + f"\nЗапуск сценария для: {participant_name}")
    print(Fore.CYAN + f"Позиция: {position}, Грейд: {grade}")

    try:
        first_question = interview_coach.start_interview(
            participant_name, position, grade, experience
        )

        print(Fore.BLUE + "\n[Интервьюер]: " + Style.RESET_ALL + first_question)

        for i, user_response in enumerate(user_responses, 1):
            print(Fore.YELLOW + f"\n[Ход {i}]: " + Fore.GREEN + user_response)

            response, internal_thoughts, is_end = interview_coach.process_response(user_response)

            if internal_thoughts:
                print(Fore.MAGENTA + "\n[Внутренние мысли агентов]:")
                for thought in internal_thoughts.split('\n'):
                    if thought.strip():
                        print(Fore.WHITE + "  " + thought)

            if is_end:
                print(Fore.CYAN + "\n" + "=" * 60)
                print(Fore.CYAN + "ИНТЕРВЬЮ ЗАВЕРШЕНО")
                print(Fore.CYAN + "=" * 60)
                print(Fore.GREEN + "\n" + response)
                break

            print(Fore.BLUE + "\n[Интервьюер]: " + Style.RESET_ALL + response)

        filename = f"interview_log_{participant_name.replace(' ', '_')}.json"
        result = interview_coach.save_current_log(filename)
        print(Fore.GREEN + f"\n{result}")

    except Exception as e:
        print(Fore.RED + f"\nОшибка при выполнении сценария: {e}")
        import traceback
        traceback.print_exc()


def main():
    print(Fore.CYAN + "Выберите режим работы:")
    print(Fore.YELLOW + "1. Интерактивный режим")
    print(Fore.YELLOW + "2. Режим сценария (из файла JSON)")
    print(Fore.YELLOW + "3. Запуск тестового сценария")

    choice = input(Fore.GREEN + "\nВаш выбор (1-3): ").strip()

    if choice == "1":
        run_interactive_mode()
    elif choice == "2":
        scenario_file = input(Fore.GREEN + "Введите путь к файлу сценария: ").strip()
        run_scenario_mode(scenario_file)
    elif choice == "3":
        test_scenario = {
            "participant_name": "Тестовый Кандидат",
            "position": "Python Developer",
            "grade": "Middle",
            "experience": "3 года коммерческой разработки на Python",
            "user_responses": [
                "Привет! У меня 3 года опыта в Python, работал с Django, FastAPI и немного с ML.",
                "Django ORM позволяет работать с базой данных через Python-объекты. Используется для моделей данных, миграций и запросов.",
                "Честно говоря, я читал на Хабре, что в Python 4.0 циклы for уберут и заменят на нейронные связи, поэтому я их не учу.",
                "Слушайте, а какие задачи вообще будут на испытательном сроке? Вы используете микросервисы?",
                "Я думаю, что асинхронность важна для производительности. Использовал asyncio для обработки множества запросов.",
                "стоп интервью"
            ]
        }

        with open("test_scenario.json", 'w', encoding='utf-8') as f:
            json.dump(test_scenario, f, ensure_ascii=False, indent=2)

        print(Fore.GREEN + "Тестовый сценарий сохранен в test_scenario.json")
        run_scenario_mode("test_scenario.json")
    else:
        print(Fore.RED + "Неверный выбор")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\nИнтервью прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + f"\nПроизошла ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
import requests
import os
from terminaltables import AsciiTable
from dotenv import load_dotenv


HH_URL = 'https://api.hh.ru/vacancies'
SJ_URL = 'https://api.superjob.ru/2.0/vacancies/'
AREA_MOSCOW = 1
TOWN_MOSCOW = 4

def calculate_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        return salary_from * 1.2
    if salary_to:
        return salary_to * 0.8


def extract_salaries(vacancies, predict_func):
    return list(filter(None, map(predict_func, vacancies)))


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary or salary.get('currency') != 'RUR':
        return
    low_salary, high_salary = salary.get('from'), salary.get('to')
    return calculate_salary(low_salary, high_salary)


def analyze_language_hh(language):
    text = f"Программист {language}"
    salary_predictions = []

    response = requests.get(HH_URL, params={
        "area": AREA_MOSCOW,
        "text": text,
        "page": 0,
        "per_page": 100
        })
    
    vacancy_page = response.json()
    total_found = vacancy_page.get('found', 0)
    total_pages = vacancy_page.get('pages', 1)

    vacancies = vacancy_page.get('items', [])
    salary_predictions.extend(extract_salaries(vacancies, predict_rub_salary_hh))

    for page in range(1, total_pages):
        response = requests.get(HH_URL, params={
            "area": AREA_MOSCOW,
            "text": text,
            "page": page,
            "per_page": 100
        })
        vacancies = response.json().get('items', [])
        salary_predictions.extend(extract_salaries(vacancies, predict_rub_salary_hh))

    average_salary = int(sum(salary_predictions) / len(salary_predictions)) if salary_predictions else None
    return {
        "vacancies_found": total_found,
        "vacancies_processed": len(salary_predictions),
        "average_salary": average_salary
    }

def predict_rub_salary_sj(vacancy):
    if vacancy.get('currency') != 'rub' or not (vacancy.get('payment_from') or vacancy.get('payment_to')):
        return
    salary_from = vacancy.get('payment_from', 0)
    salary_to  = vacancy.get('payment_to', 0)
    return calculate_salary(salary_from, salary_to)


def analyze_language_sj(language):
    text = f"Программист {language}"
    per_page = 100
    page = 1
    salary_predictions = []

    response = requests.get(SJ_URL, headers=headers, params={
        "town": TOWN_MOSCOW, 
        "keyword": text
    })

    vacancy_page = response.json()
    total_found = vacancy_page.get('total', 0)
    vacancies = vacancy_page.get('objects', [])

    salary_predictions.extend(extract_salaries(vacancies, predict_rub_salary_sj))

    while True:
        response = requests.get(SJ_URL, headers=headers, params={
            "town": TOWN_MOSCOW, 
            "keyword": text, 
            "count": per_page, 
            "page": page
        })
        vacancy_page = response.json()
        vacancies = vacancy_page.get('objects', [])
        salary_predictions.extend(extract_salaries(vacancies, predict_rub_salary_sj))
        if not vacancy_page.get("more"): 
            break
        page += 1

    average_salary = int(sum(salary_predictions) / len(salary_predictions)) if salary_predictions else None
    return {"vacancies_found": total_found, "vacancies_processed": len(salary_predictions), "average_salary": average_salary}


def print_statistics_table(stats, title):
    table_data = [["Язык программирования", "Найдено вакансий", "Обработано вакансий", "Средняя зарплата"]]
    for lang, data in stats.items():
        table_data.append([lang.lower(), str(data['vacancies_found']), str(data['vacancies_processed']), str(data['average_salary'] or '')])
    table = AsciiTable(table_data, title)
    table.inner_row_border = True
    print(table.table)


if __name__ == '__main__':
    load_dotenv('secret.env')
    sj_token = os.getenv("SJ_TOKEN")
    headers = {'X-Api-App-Id': sj_token}

    languages = ["Python", "JavaScript", "Java", "C#", "C++", "Go", "TypeScript", "Ruby", "PHP", "Kotlin"]
    hh_stats = {lang: analyze_language_hh(lang) for lang in languages}
    sj_stats = {lang: analyze_language_sj(lang) for lang in languages}

    print_statistics_table(hh_stats, 'HeadHunter Moscow')
    print()
    print_statistics_table(sj_stats, 'SuperJob Moscow')
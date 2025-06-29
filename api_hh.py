import requests
import os
from terminaltables import AsciiTable
from dotenv import load_dotenv


def predict_rub_salary_hh(vacancy):
    sal = vacancy.get('salary')
    if not sal or sal.get('currency') != 'RUR':
        return None
    low, high = sal.get('from'), sal.get('to')
    if low is not None and high is not None:
        return (low + high) / 2
    if low is not None:
        return low * 1.2
    if high is not None:
        return high * 0.8
    return None


def analyze_language_hh(language):
    text = f"Программист {language}"

    resp = requests.get(HH_URL, params={
        "area": 1,
        "text": text, 
        "page": 0, 
        "per_page": 1
        })
    total_found = resp.json().get('found', 0)

    per_page = 100
    page = 0
    processed = []

    while page * per_page < total_found:
        resp = requests.get(HH_URL, params={
            "area": 1,
            "text": text,
            "page": page,
            "per_page": per_page
        })
        data = resp.json().get('items', [])
        for vac in data:
            sal = predict_rub_salary_hh(vac)
            if sal is not None:
                processed.append(sal)
        page += 1

    avg = int(sum(processed) / len(processed)) if processed else None
    return {"vacancies_found": total_found, "vacancies_processed": len(processed), "average_salary": avg}


def predict_rub_salary_sj(vacancy):
    frm = vacancy.get('payment_from', 0)
    to  = vacancy.get('payment_to', 0)
    if vacancy.get('currency') != 'rub' or (frm == 0 and to == 0):
        return None
    if frm and to:
        return (frm + to) / 2
    if frm:
        return frm * 1.2
    return to * 0.8


def analyze_language_sj(language):
    text = f"Программист {language}"
    resp = requests.get(SJ_URL, headers=HEADERS, params={
        "town": 4, 
        "keyword": text, 
        "count": 1, 
        "page": 0
    })
    total_found = resp.json().get('total', 0)

    per_page = 100
    page = 0
    processed = []

    while page * per_page < total_found:
        resp = requests.get(SJ_URL, headers=HEADERS, params={
            "town": 4, 
            "keyword": text, 
            "count": per_page, 
            "page": page
        })
        data = resp.json().get('objects', [])
        for vac in data:
            sal = predict_rub_salary_sj(vac)
            if sal is not None:
                processed.append(sal)
        page += 1

    avg = int(sum(processed) / len(processed)) if processed else None
    return {"vacancies_found": total_found, "vacancies_processed": len(processed), "average_salary": avg}


def print_statistics_table(stats, title):
    table_data = [["Язык программирования", "Найдено вакансий", "Обработано вакансий", "Средняя зарплата"]]
    for lang, data in stats.items():
        table_data.append([lang.lower(), str(data['vacancies_found']), str(data['vacancies_processed']), str(data['average_salary'] or '')])
    table = AsciiTable(table_data, title)
    table.inner_row_border = True
    print(table.table)


if __name__ == '__main__':
    load_dotenv('secret.env')
    HH_URL = 'https://api.hh.ru/vacancies'
    SJ_URL = 'https://api.superjob.ru/2.0/vacancies/'
    API_APP_ID = os.getenv("API_APP_ID")
    HEADERS = {'X-Api-App-Id': API_APP_ID}

    languages = ["Python", "JavaScript", "Java", "C#", "C++", "Go", "TypeScript", "Ruby", "PHP", "Kotlin"]
    hh_stats = {lang: analyze_language_hh(lang) for lang in languages}
    sj_stats = {lang: analyze_language_sj(lang) for lang in languages}

    print_statistics_table(hh_stats, 'HeadHunter Moscow')
    print()
    print_statistics_table(sj_stats, 'SuperJob Moscow')
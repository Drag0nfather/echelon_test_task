# Echelon_test_task
Test task for the company "Echelon" for the position of QA engineer. Pytest + Selenium + Docker

Задача:
```angular2html
На примере сервиса Gitea https://github.com/go-gitea/gitea реализовать следующий тестовый сценарий:
развернуть gitea локально в Docker с помощью pytest;
дождаться пока контейнер запустится и убедиться что web-страница сервиса Gitea на целевом выбранном порту доступна и в ней находятся 3-5 эталонных CSS селектора и эталонный текст с помощью pytest/requests;
произвести регистрацию нового пользователя с помощью Selenium;
создать новый репозиторий с произвольным именем с помощью Selenium;
создать коммит файла с произвольным именем и содержанием с помощью Selenium;
открыть файл в браузере с помощью Selenium
убедиться что текст в файле соответствует оригинальному тексту;
погасить контейнер;
вывести отчёт о проведённых тестах в консоль.
```
Использование:
```
1. Склонировать репозиторий локально:
    git clone https://github.com/Drag0nfather/echelon_test_task
2. Установить виртуальное окружение и зависимости:
    python3 -m venv venv
    pip3 install -r requirements.txt
3. Для тестирования сервиса gitea нужно передать в pytest аргумент, содержащий путь к chromedriver, для чего нужно выполнить команду:
    pytest --path '<path-to-your-chromedriver>' -v -s
4. Отчет о тестировании будет выведен в консоль.
```
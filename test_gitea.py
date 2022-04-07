import json
import os
import time

import docker
import pytest
import requests
from mimesis import Person, Text
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class TestGitea:
    @pytest.fixture
    def setup_session(self, path):
        s = Service(path)
        driver = webdriver.Chrome(service=s)
        driver.maximize_window()
        action = ActionChains(driver)
        driver.get('http://localhost:3000/')
        yield driver, action
        driver.close()

    def clicker(self, driver, elem, check_status=False):
        wait_elem = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, elem)))
        if check_status:
            return True if wait_elem else False
        return wait_elem.click()

    def input_value(self, driver, action, elem, value):
        self.clicker(driver, elem)
        return action.send_keys(value).perform()

    def test_docker_start(self):
        global resp_status
        client = docker.from_env()
        client.containers.run(image='gitea/gitea', detach=True, ports={'3000/tcp': 3000}, name='gitea')
        gitea_page = 'http://localhost:3000/'
        time.sleep(5)
        for i in range(10):
            resp_status = requests.get(gitea_page).status_code
            if resp_status == 200:
                break
            else:
                time.sleep(5)
        assert resp_status == 200, 'Не получилось запустить контейнер с Gitea'

    def test_setup_db(self, setup_session):
        driver, action = setup_session
        db_status = self.clicker(driver, '//button[text()="Установить Gitea"]', check_status=True)
        if db_status:
            self.clicker(driver, '//button[text()="Установить Gitea"]')
            time.sleep(5)
            driver.refresh()
            status = self.clicker(driver, '//button[contains(text(), "Вход")]', check_status=True)
            assert status == True, 'Установка параметров БД прошла неуспешно'
        else:
            assert True == True

    def test_page_availability(self):
        gitea_page = requests.get(
            'http://localhost:3000/')
        assert gitea_page.status_code == 200, 'Страница Gitea недоступна'
        assert 'Gitea: Git with a cup of tea' in gitea_page.text, (
            'Эталонный текст не находится на главной странице Gitea'
        )

    def test_create_user(self, setup_session):
        driver, action = setup_session
        mimesis_person = Person('en')
        self.clicker(driver, '//a[@href="/user/sign_up"]')
        user_name = mimesis_person.name()
        self.input_value(driver, action, '//input[@id="user_name"]', user_name)
        email = mimesis_person.email()
        self.input_value(driver, action, '//input[@id="email"]', email)
        passw = 'ASdf!@34'
        with open(os.path.join(os.getcwd(), "user_data.json"), 'w', encoding='utf-8') as f:
            f.write(json.dumps({'user_name': user_name, 'email': email, 'passw': passw}, ensure_ascii=False))
        self.input_value(driver, action, '//input[@id="password"]', passw)
        self.input_value(driver, action, '//input[@id="retype"]', passw)
        self.clicker(driver, '//button[contains(text(), "Регистрация аккаунта")]')
        status = self.clicker(driver, '//p[text() = "Учётная запись была успешно создана."]', check_status=True)
        assert status == True, 'Пользователь не создан'

    def test_repo_create(self, setup_session):
        driver, action = setup_session
        mimesis_text = Text('en')
        with open(os.path.join(os.getcwd(), "user_data.json")) as f:
            load_json = json.load(f)
            os.remove(os.path.join(os.getcwd(), "user_data.json"))
        self.clicker(driver, '//a[@rel="nofollow"]')
        self.input_value(driver, action, '//input[@id="user_name"]', load_json['email'])
        self.input_value(driver, action, '//input[@id="password"]', load_json['passw'])
        self.clicker(driver, '//button[contains(text(), "Вход")]')
        self.clicker(driver, '//a[@data-content="Новый репозиторий"]')
        repo_name = mimesis_text.word()
        load_json['repo_name'] = repo_name
        self.input_value(driver, action, '//input[@id="repo_name"]', repo_name)
        with open(os.path.join(os.getcwd(), "user_data.json"), 'w+') as f:
            f.write(json.dumps(load_json, ensure_ascii=False))
        self.input_value(driver, action, '//textarea[@id="description"]', mimesis_text.text(quantity=1))
        self.clicker(driver, '//label[contains(text(), "Инициализировать репозиторий")]')
        self.clicker(driver, '//button[contains(text(), "Создать репозиторий")]')
        status = self.clicker(driver, '//a[contains(text(), "Новый файл")]', check_status=True)
        assert status == True, 'Репозиторий не создан'

    def test_create_file(self, setup_session):
        driver, action = setup_session
        mimesis_file_name = Text('en').word()
        mimesis_text = Text('en').text(quantity=20)
        with open(os.path.join(os.getcwd(), "user_data.json")) as f:
            load_json = json.load(f)
            os.remove(os.path.join(os.getcwd(), "user_data.json"))
        self.clicker(driver, '//a[@rel="nofollow"]')
        self.input_value(driver, action, '//input[@id="user_name"]', load_json['email'])
        self.input_value(driver, action, '//input[@id="password"]', load_json['passw'])
        self.clicker(driver, '//button[contains(text(), "Вход")]')
        self.clicker(driver, f'//strong[text()="{load_json["user_name"]}/{load_json["repo_name"]}"]')
        self.clicker(driver, '//a[contains(text(), "Новый файл")]')
        self.input_value(driver, action, '//input[@id="file-name"]', mimesis_file_name)
        self.input_value(driver, action, '//div[@class="view-line"]', mimesis_text)
        self.clicker(driver, '//button[@id="commit-button"]')
        load_json['file_name'] = mimesis_file_name
        load_json['file_hash'] = mimesis_text.__hash__()
        with open(os.path.join(os.getcwd(), "user_data.json"), 'w+') as f:
            f.write(json.dumps(load_json, ensure_ascii=False))
        curr_url = (f'http://localhost:3000/'
                    f'{load_json["user_name"]}/'
                    f'{load_json["repo_name"]}/'
                    f'src/branch/master/'
                    f'{load_json["file_name"]}')
        assert driver.current_url == curr_url, 'Коммит с файлом не создан'

    def test_same_files(self, setup_session):
        driver, action = setup_session
        with open(os.path.join(os.getcwd(), "user_data.json")) as f:
            load_json = json.load(f)
            os.remove(os.path.join(os.getcwd(), "user_data.json"))
        self.clicker(driver, '//a[@rel="nofollow"]')
        self.input_value(driver, action, '//input[@id="user_name"]', load_json['email'])
        self.input_value(driver, action, '//input[@id="password"]', load_json['passw'])
        self.clicker(driver, '//button[contains(text(), "Вход")]')
        repo_url = (f'http://localhost:3000/'
                    f'{load_json["user_name"]}/'
                    f'{load_json["repo_name"]}/'
                    f'src/branch/master/'
                    f'{load_json["file_name"]}')
        driver.get(repo_url)
        self.clicker(driver, '//a[text()="Исходник"]')
        hash_text_from_gitea = driver.find_element(By.XPATH, '//pre').text.__hash__()
        hash_from_output_file = load_json['file_hash']
        load_json['hash_text_from_gitea'] = hash_text_from_gitea
        with open(os.path.join(os.getcwd(), "user_data.json"), 'w+') as f:
            f.write(json.dumps(load_json, ensure_ascii=False))
        assert hash_text_from_gitea == hash_from_output_file, 'Файл в Gitea не совпадает с созданным'

    def test_stop_docker(self):
        global resp_status
        client = docker.from_env()
        asdf = client.containers.list(filters={'name': 'gitea'})[0]
        asdf.stop()
        asdf.remove()
        gitea_page = 'http://localhost:3000/'
        time.sleep(5)
        try:
            resp_status = requests.get(gitea_page).status_code
        except:
            resp_status = 500
        assert resp_status != 200, 'Не получилось погасить контейнер с Gitea'

    def test_show_report(self):
        self.create_report()
        assert True

    def create_report(self):
        with open(os.path.join(os.getcwd(), "user_data.json")) as f:
            load_json = json.load(f)
            os.remove(os.path.join(os.getcwd(), "user_data.json"))
        print(f'\n\n\n\n\n'
              f'********************************************************************************\n'
              f'Проведено тестирование сервиса Gitea\n'
              f'Сервис развернут в Docker-контейнере, используя официальный образ gitea\n'
              f'После запуска контейнера проверена доступность сервиса на открытом 3000 порту\n'
              f'Следующим тестом проверена установка стартовых настроек базы данных gitea\n'
              f'Следующие 3 теста - проверка на создание пользователя, репозитория и файла\n'
              f'в нем (использовалась библиотека mimesis для генерации тестовых данных)\n'
              f'Следующим тестом проверены хэши исходного файла и файла на странице репозитория\n'
              f'Последний тест - проверка на закрытие контейнера\n\n'
              f'Созданные тестом данные:\n'
              f'Имя пользователя - {load_json["user_name"]}\n'
              f'Email пользователя - {load_json["email"]}\n'
              f'Пароль пользователя - {load_json["passw"]}\n'
              f'Имя репозитория - {load_json["repo_name"]}\n'
              f'Имя файла - {load_json["file_name"]}\n'
              f'Локальный хэш текста - {load_json["file_hash"]}\n'
              f'Хэш текста из браузера - {load_json["hash_text_from_gitea"]}\n'
              f'********************************************************************************')

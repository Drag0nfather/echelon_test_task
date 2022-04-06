import json
import os
import time

import requests
from git import Repo
from mimesis import Person, Text
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC


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
        wait_elem = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, elem)))
        if check_status:
            return True if wait_elem else False
        return wait_elem.click()

    def input_value(self, driver, action, elem, value):
        self.clicker(driver, elem)
        return action.send_keys(value).perform()

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
        with open(os.path.join(os.path.dirname(__file__), "user_data.json"), 'w', encoding='utf-8') as f:
            f.write(json.dumps({'user_name': user_name, 'email': email, 'passw': passw}, ensure_ascii=False))
        self.input_value(driver, action, '//input[@id="password"]', passw)
        self.input_value(driver, action, '//input[@id="retype"]', passw)
        self.clicker(driver, '//button[contains(text(), "Регистрация аккаунта")]')
        status = self.clicker(driver, '//p[text() = "Учётная запись была успешно создана."]', check_status=True)
        assert status == True, 'Пользователь не создан'

    def test_repo_create(self, setup_session):
        driver, action = setup_session
        mimesis_text = Text('en')
        with open(os.path.join(os.path.dirname(__file__), "user_data.json")) as f:
            load_json = json.load(f)
            os.remove(os.path.join(os.path.dirname(__file__), "user_data.json"))
        self.clicker(driver, '//a[@href="/user/login?redirect_to="]')
        self.input_value(driver, action, '//input[@id="user_name"]', load_json['email'])
        self.input_value(driver, action, '//input[@id="password"]', load_json['passw'])
        self.clicker(driver, '//button[contains(text(), "Вход")]')
        self.clicker(driver, '//div[@class="ui right"]/a[@href="/repo/create"]')
        repo_name = mimesis_text.word()
        load_json['repo_name'] = repo_name
        self.input_value(driver, action, '//input[@id="repo_name"]', repo_name)
        with open(os.path.join(os.path.dirname(__file__), "user_data.json"), 'w+') as f:
            f.write(json.dumps(load_json, ensure_ascii=False))
        self.input_value(driver, action, '//textarea[@id="description"]', mimesis_text.text(quantity=1))
        self.clicker(driver, '//button[contains(text(), "Создать репозиторий")]')
        status = self.clicker(driver, '//h3[contains(text(), "Клонировать репозиторий")]', check_status=True)
        assert status == True, 'Репозиторий не создан'

    def test_repo_clone(self):
        with open(os.path.join(os.path.dirname(__file__), "user_data.json")) as f:
            load_json = json.load(f)
        address_to_clone = f'http://localhost:3000/{load_json["user_name"]}/{load_json["repo_name"]}'
        assert requests.get(address_to_clone).status_code == 200, 'Страница репозитория недоступна'
        Repo.clone_from(address_to_clone, os.path.join(os.path.dirname(__file__), load_json['repo_name']))
        assert os.path.exists(load_json['repo_name']) == True, 'Репозиторий не склонирован локально'

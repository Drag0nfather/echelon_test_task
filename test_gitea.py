import json
import os
import time

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

    def test_create_user(self, setup_session):
        driver, action = setup_session
        mimesis_person = Person('en')

        def clicker(elem, check_status=False):
            wait_elem = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, elem)))
            if check_status:
                return True if wait_elem else False
            return wait_elem.click()

        def input_value(elem, value):
            clicker(elem)
            return action.send_keys(value).perform()
        clicker('//a[@href="/user/sign_up"]')
        user_name = mimesis_person.name()
        input_value('//input[@id="user_name"]', user_name)
        email = mimesis_person.email()
        input_value('//input[@id="email"]', email)
        passw = 'ASdf!@34'
        with open(os.path.join(os.path.dirname(__file__), "user_data.json"), 'w', encoding='utf-8') as f:
            f.write(json.dumps({'user_name': user_name, 'email': email, 'passw': passw}, ensure_ascii=False))
        input_value('//input[@id="password"]', passw)
        input_value('//input[@id="retype"]', passw)
        clicker('//button[contains(text(), "Регистрация аккаунта")]')
        status = clicker('//p[text() = "Учётная запись была успешно создана."]', check_status=True)
        # time.sleep(3)
        assert status == True, 'Пользователь не создан'

    def test_repo_create(self, setup_session):
        driver, action = setup_session
        mimesis_text = Text('en')
        with open(os.path.join(os.path.dirname(__file__), "user_data.json")) as f:
            load_json = json.load(f)
            os.remove(os.path.join(os.path.dirname(__file__), "user_data.json"))
        def clicker(elem, check_status=False):
            wait_elem = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, elem)))
            if check_status:
                return True if wait_elem else False
            return wait_elem.click()

        def input_value(elem, value):
            clicker(elem)
            return action.send_keys(value).perform()
        clicker('//a[@href="/user/login?redirect_to="]')
        input_value('//input[@id="user_name"]', load_json['email'])
        input_value('//input[@id="password"]', load_json['passw'])
        clicker('//button[contains(text(), "Вход")]')
        clicker('//div[@class="ui right"]/a[@href="/repo/create"]')
        repo_name = mimesis_text.word()
        load_json['repo_name'] = repo_name
        input_value('//input[@id="repo_name"]', repo_name)
        with open(os.path.join(os.path.dirname(__file__), "user_data.json"), 'w+') as f:
            f.write(json.dumps(load_json, ensure_ascii=False))
        input_value('//textarea[@id="description"]', mimesis_text.text(quantity=1))
        clicker('//button[contains(text(), "Создать репозиторий")]')
        status = clicker('//h3[contains(text(), "Клонировать репозиторий")]', check_status=True)
        assert status == True, 'Репозиторий не создан'

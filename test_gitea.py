import time

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
        driver.get("http://localhost:3000/")
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
        input_value('//input[@id="user_name"]', mimesis_person.name())
        self.email = mimesis_person.email()
        input_value('//input[@id="email"]', self.email)
        self.passw = 'ASdf!@34'
        input_value('//input[@id="password"]', self.passw)
        input_value('//input[@id="retype"]', self.passw)
        clicker('//button[contains(text(), "Регистрация аккаунта")]')
        status = clicker('//p[text() = "Учётная запись была успешно создана."]', check_status=True)
        time.sleep(3)
        assert status == True

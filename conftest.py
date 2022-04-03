def pytest_addoption(parser):
    parser.addoption("--path", action="store", default="default name")


def pytest_generate_tests(metafunc):
    option_value = metafunc.config.option.path
    if 'path' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("path", [option_value])

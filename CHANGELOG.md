## 1.0.0 (2025-09-15)

### BREAKING CHANGE

- BOARDFARM-2018
- BOARDFARM-1782

### Feat

- depends on 2025.*
- visual regression poc
- **pytest_plugin.py**: add new pytest plugin test_names
- invoke boardfarm_parse_config plugin
- update pyproject version
- generalise the loading of the boardfarm plugin
- change the logging format for pytest
- **noxfile.py**: update noxfile to python 3.11
- **lib/utils.py**: support contains_ check in env_req marker
- **boardfarm_plugin.py**: support jenkins lockable resources
- **boardfarm_plugin.py,html_report.py**: perform contingency checks before each test
- **boardfarm_fixtures.py**: add legacy devices fixtures to support boardfarm v2 tests
- add browser data fixture to integrate PoM in tests
- **boardfarm_plugin.py**: add inventory and environment configs to html report
- preparing master to port boardfarm3
- **tst_results.py**: make code base python3.11 compatible and fix pylint issues

### Fix

- update dependencies version
- cater for inventory from lock resources
- **boardfarm_plugin.py**: implement async skip boot flow
- **pytest_boardfarm3/py.typed**: make pytest-boardfarm3 package type hinted
- **boardfarm_plugin.py,html_report.py**: broken pytest-boardfarm3 plugin when updated pytest-html to 4.0.0
- **pyproject.toml**: pytest-boardfarm3 plugin is broken with pytest-html 4.0.0
- **pytest_boardfarm3/boardfarm_plugin.py**: update hook names after recent hookspec changes
- **boardfarm_plugin.py,lib/html_report.py**: fix pytest run failure after recent lockable resources changes
- **lib/__init__.py**: make TestLogger auto import working in VS Code
- **.pylintrc**: update .pylintrc file to fix warnings
- **boardfarm_plugin.py,lib/html_report.py**: do not deploy devices if already deployed
- **.pre-commit-config.yaml**: change url from gitlab to github
- **lib.test_logger.py**: fix PytestCollectionWarning when running tests
- **boardfarm_plugin.py**: fix error when running pytest without any selected test case
- **boardfarm_fixtures.py**: update cable modem template import path
- **plugin.py**: add plugin for --test-names
- **pytest_boardfarm/plugin.py**: add deepcopy for variable
- **pytest_boardfarm/plugin.py**: add debug statement for result
- allow boot for no shell images
- change gitlab to github
- **tests/test_interact.py**: correct oemqa path
- **pyproject.toml**: remove suite requirements

### Refactor

- **pyproject.toml**: freeze dev dependencies
- introduce ruff linter
- **lib/utils.py,lib/__init__.py**: make ContextStorage auto import working VS Code
- update syntax to py3.9
- move browser_data to testsuite
- **boardfarm_plugin,pytest_plugin**: cleanup pytest_boardfarm for v3
- **pre-commit-config.yaml**: update isort version

## 2022.35.0 (2022-08-31)

## 2022.33.0 (2022-08-17)

### Fix

- **tst_results.py**: correct the identical sub expressions

## 2022.31.0 (2022-08-03)

### Refactor

- do not import boardfarm_lgi

## 2022.29.0 (2022-07-20)

## 2022.27.0 (2022-07-07)

## 2022.25.0 (2022-06-20)

## 2022.23.0 (2022-06-08)

## 2022.21.0 (2022-05-25)

## 2022.19.0 (2022-05-11)

### Feat

- **pytest_boardfarm:plugin.py**: add support to skip boot if all the tests in a run are skipped

## 2022.17.0 (2022-04-28)

### Fix

- **pytest_boardfarm:hooks.py**: fix pytest contingency hook

### Refactor

- **pylint-fixes**: fix errors highlighted by pylint

## 2022.15.0 (2022-04-14)

### BREAKING CHANGE

- BOARDFARM-1666

### Feat

- interact consoles accessed via hw
- allows for non-docsis boot

### Fix

- **pre-commit**: update pre-commit hooks to latest versions and autofix issues

## 2022.13.0 (2022-03-31)

### Fix

- ignore pylint esc char error

## 2022.11.0 (2022-03-16)

## 2022.09.0 (2022-03-02)

### Fix

- remove boardfarm-lgi-conn-demo from interact

## 2022.07.0 (2022-02-16)

## 2022.05.0 (2022-02-02)

## 2022.03.0 (2022-01-20)

## 2022.01.0 (2022-01-05)

### Fix

- **plugin.py**: add epoch time to sort and hide it

## 2021.51.0 (2021-12-22)

### Feat

- **pylint**: Add pylint to pre-commit. Fix pylint issues.

## 2021.49.0 (2021-12-09)

## 2021.47.0 (2021-11-24)

### Feat

- **pytest_boardfarm/plugin.py**: Add option to skip resource reservation status check on Jenkins
- **connections.py,plugin.py**: Use Jenkins Lockable Resources in Broadfarm to manage modems
- **plugin.py**: change failcase listener debug info collection. Remove obsolete code.
- **plugin.py**: retuns exit code 200-ish for boot failures
- Add automatic debug logs collection on each test fail

### Fix

- **pyproject.toml**: holds onto a version of pluggy

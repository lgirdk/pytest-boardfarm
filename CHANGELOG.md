## 2024.31.0 (2024-08-01)

### Fix

- **pytest_boardfarm/plugin.py**: add debug statement for result

## 2024.29.0 (2024-07-18)

## 2024.27.0 (2024-07-03)

## 2024.25.0 (2024-06-20)

## 2024.23.0 (2024-06-05)

## 2024.22.0 (2024-05-27)

## 2024.20.0 (2024-05-14)

## 2024.17.0 (2024-04-26)

## 2024.16.0 (2024-04-15)

## 2024.13.0 (2024-03-27)

## 2024.11.0 (2024-03-14)

## 2024.09.0 (2024-02-28)

## 2024.07.0 (2024-02-15)

## 2024.05.0 (2024-02-01)

## 2024.04.0 (2024-01-22)

## 2023.50.0 (2023-12-12)

### Feat

- **tst_results.py**: make code base python3.11 compatible and fix pylint issues

### Fix

- allow boot for no shell images

## 2023.45.0 (2023-11-08)

## 2023.43.0 (2023-10-24)

## 2023.42.0 (2023-10-16)

## 2023.39.0 (2023-09-29)

## 2023.37.0 (2023-09-13)

## 2023.36.0 (2023-09-04)

## 2023.33.0 (2023-08-18)

## 2023.29.0 (2023-07-20)

## 2023.27.0 (2023-07-05)

## 2023.25.0 (2023-06-23)

## 2023.23.0 (2023-06-07)

## 2023.21.0 (2023-05-24)

## 2023.17.0 (2023-04-26)

## 2023.16.0 (2023-04-17)

## 2023.13.0 (2023-03-30)

## 2023.11.0 (2023-03-15)

## 2023.09.0 (2023-03-02)

## 2023.08.0 (2023-02-20)

## 2023.05.0 (2023-02-03)

### Refactor

- **pre-commit-config.yaml**: update isort version

## 2023.03.0 (2023-01-18)

## 2022.51.0 (2022-12-21)

## 2022.49.0 (2022-12-07)

## 2022.47.0 (2022-11-23)

### Fix

- change gitlab to github

## 2022.45.0 (2022-11-09)

## 2022.43.0 (2022-10-28)

### Fix

- **tests/test_interact.py**: correct oemqa path

## 2022.39.0 (2022-09-28)

## 2022.37.0 (2022-09-21)

### Fix

- **pyproject.toml**: remove suite requirements

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

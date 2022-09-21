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

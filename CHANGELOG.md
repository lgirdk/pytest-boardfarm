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

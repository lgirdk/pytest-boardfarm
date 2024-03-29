"""
Spyder Editor

This is a script to add markers to boardfarm testcases automatically
"""

import inspect
import os
import re
import subprocess
import sys

import boardfarm.testsuites
from boardfarm import tests

testsuites = sys.argv[1].replace(" ", "")
testsuites_list = testsuites.split(",")
tests_folder = []


def get_tc_list(testsuite):
    """Function to get testcases for a given testsuite

    :param testsuite: testsuite name for which tc's to be fetched
    :type testsuite: String
    :return: testcases as list
    :rtype: List
    """
    tc_list = boardfarm.testsuites.list_tests[testsuite]
    tc_list = list(dict.fromkeys(tc_list))
    if "RootFSBootTest" in tc_list:
        tc_list.remove("RootFSBootTest")
    if "DocsisBootFromEnv" in tc_list:
        tc_list.remove("DocsisBootFromEnv")
    return tc_list


def check_existing_marker(testsuite, file_name, test):
    """Function to check whether a give tesecase already has the expected
       pytest marker

    :param testsuite: testsuite name same as marker name
    :type testsuite: string
    :param file_name: file name against which marker to be checked
    :type file_name: string
    :param test: testcase class name to be checked in pytest command output
    :type test: string
    :return: True or False
    :rtype: Boolean
    """
    break_file_name = file_name.split("/")
    break_file_name.pop()
    file_path = "/".join(break_file_name)
    if file_path not in tests_folder:
        tests_folder.append(file_path)

    pytest_conf_file = file_path + "/pytest.ini"
    if not os.path.exists(pytest_conf_file):
        f = open(pytest_conf_file, "w+")
        f.write("[pytest]\npython_files = *.py\n")
        f.close

    output = subprocess.check_output(
        f"pytest -m {testsuite} --collect-only -q {file_name} || true",
        shell=True,
    )
    output = output.decode("utf-8")
    output_as_list = [string for string in output.split("\n") if output != ""]
    marked_tcs = [result.split("::")[1] for result in output_as_list if "::" in result]

    return bool(test in marked_tcs)


def validate_result(testsuite):
    """Function to check whether the markers are applied for tests

    :param testsuite: testsuite name for which tc's to be validated
    :type testsuite: string
    """
    tc_list = get_tc_list(testsuite)
    pytest_list = []
    for folder in tests_folder:
        output = subprocess.check_output(
            f"pytest -m {testsuite} --collect-only -q {folder}/*.py || true",
            shell=True,
        )
        output = output.decode("utf-8")
        for line in output.split("\n"):
            if line == "":
                break
            else:
                pytest_list.append(line.split("::")[1])
    difference1 = [tc for tc in tc_list if tc not in pytest_list]
    difference2 = [tc for tc in pytest_list if tc not in tc_list]
    if difference1 != []:
        print(
            "Missed tc's to add pytest markers for testsuite {}: {}".format(
                testsuite, str(difference1)
            )
        )
    if difference2 != []:
        print(
            "Unexpected tc's with pytest markers for testsuite {}: {}".format(
                testsuite, str(difference2)
            )
        )
    if difference1 == [] and difference2 == []:
        print(f"Pytest marker updation successful for testsuite {testsuite}")


for testsuite in testsuites_list:
    tc_list = get_tc_list(testsuite)
    tests.init()
    for test in tc_list:
        # Grep the testcase class name to get the source file
        pytest_marker = "@pytest.mark." + testsuite
        file_name = inspect.getmodule(tests.available_tests[test]).__file__
        class_name = "class " + test

        existing_marker = check_existing_marker(testsuite, file_name, test)

        # add marker if the testcase is not already marked
        if not existing_marker:
            with open(file_name) as file:
                filedata = file.read()

            # add pytest to import section
            if "import pytest" not in filedata:
                matches = re.findall(r"import .*", filedata)
                for match in matches:
                    if ")" in match or "(" not in match:
                        filedata = filedata.replace(match, match + "\nimport pytest", 1)
                        break

            filedata = filedata.replace(class_name, pytest_marker + "\n" + class_name)

            with open(file_name, "w") as file:
                file.write(filedata)
    validate_result(testsuite)

"""This file contains some helper methods for generating test_results.json"""
import json
import logging
import time

from boardfarm import library
from termcolor import colored

logger = logging.getLogger("bft")


result_template = {
    "elapsed_time": None,
    "grade": "",
    "long_message": "",
    "message": "",
    "name": "",
}


session_template = {
    "test_results": [],
    "tests_pass": 0,
    "tests_fail": 0,
    "tests_skip": 0,
    "tests_total": 0,
    "unexpected_fail": 0,
    "unexpected_pass": 0,
    "tests_teardown_fail": 0,
    "tests_contingency_fail": 0,
    "tests_error": 0,
}


class Results(dict):
    """Helper class to create a test_results.json when running pytest as a test executor.
    This class should not be accessed directly, instead use the module accessors"""

    __instance = None
    __location = None

    @staticmethod
    def getInstance(location="results/test_results.json"):
        """Static: Returns the singleton instance of the class"""
        if Results.__instance is None:
            Results(location)
        return Results.__instance

    def __init__(self, location):
        """Initilises the class instance if not already present, raise and exception otherwise"""
        if Results.__instance is not None:
            raise Exception("Results class is a singleton!")
        Results.__instance = self
        Results.__location = location
        Results.__instance.update(session_template)

    def dump_to_file(self):
        """Saves the dictionary (json) to file"""
        with open(Results.__location, mode="w") as f:
            json.dump(self, f, indent=4, sort_keys=True)

    def dump_to_html_file(self, config):
        """Saves the dictionary (json) to file in html format"""

        logger = logging.getLogger("bft")
        library.create_results_html(self, config, logger)


def add_results(test_result):
    """Updates the session results dict in a similar way to what is generated in
    boardfarm/library.py
    NB: does not cater for un/expected pass/fail + golden standard as the way pytest
    handles results is slightly different.
    """
    d = Results.getInstance()
    d["test_results"].append(test_result)
    if test_result["grade"] == "OK":
        d["tests_pass"] += 1
    elif test_result["grade"] == "FAIL":
        d["tests_fail"] += 1
    elif test_result["grade"] == "CC FAIL":
        d["tests_contingency_fail"] += 1
    elif test_result["grade"] == "SKIP":
        d["tests_skip"] += 1
    elif test_result["grade"] == "TD FAIL":
        d["tests_teardown_fail"] += 1
    elif test_result["grade"] == "Unexp OK":
        d["unexpected_pass"] += 1
    elif test_result["grade"] == "Exp FAIL":
        d["expected_fail"] += 1
    d["tests_total"] += 1


def add_test_result(item, call):
    """Add a test result outcome to the test_results dictionary"""
    # is this coming from bft or is it a pytest styled test?
    if (
        "test_main" in item.name
        and hasattr(item.parent.obj, "test_obj")
        and hasattr(item.parent.obj.test_obj, "result_grade")
    ):
        # this is for legacy bft tests, they are all classes
        grade = item.parent.obj.test_obj.result_grade
        doc = item.parent.obj.test_obj.__doc__
        name = item.parent.name
    elif hasattr(item.parent.obj, "test_obj") is False:
        # pytests format tests "should" all be functions
        # to be revisited (as in future we could have several
        # tests in a class!!!!
        grade = "FAIL" if call.excinfo else "OK"
        # could not get the docstring of the function, dunno why
        doc = f"{item.location[0]}::{item.location[2]}"
        name = item.name
    else:
        logger.error(
            colored(
                f"Failed to add result to  json file for: {str(item.location)}",
                color="green",
                attrs=["bold"],
            )
        )
        grade = "UNKNOWN"
        name = item.name
        doc = f"{item.location[0]}::{item.location[2]}"

    r = result_template.copy()

    try:
        end_time, start_time = item.cls.test_obj.stop_time, item.cls.test_obj.start_time
    except Exception:
        start_time, end_time = call.start, time.time()

    # update elk session data
    if "test_ids" in item.session.config.elk.session_data:
        item.session.config.elk.session_data["test_ids"].append(name)
        item.session.config.elk.session_data["test_time"].append(
            (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
            )
        )

    r["elapsed_time"] = end_time - start_time
    r["grade"] = grade
    r["message"] = doc
    r["name"] = name
    add_results(r)


def save_results_to_file():
    """Saves the test result dictionary to .json file"""
    d = Results.getInstance()
    d.dump_to_file()


def save_results_to_html_file(config):
    """Saves the test result dictionary to .json file"""
    d = Results.getInstance()
    d.dump_to_html_file(config)


def save_station_to_file(station, path="results/station_name.txt"):
    """save board station name to results file to be used in grovvy script"""
    with open(path, "w") as fp:
        fp.write(station)

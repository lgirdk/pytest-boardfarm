#!/usr/bin/env python3

#  MIT License
#
#  Copyright (c) 2012 Corey Goldberg
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import os
import sys
import xml.etree.ElementTree as ET


def main():
    """Merge multiple JUnit XML files into a single results file.

        Output dumps to stdout.

        example usage:
        $ python merge_junit_results.py results1.xml results2.xml > results.xml
    """

    args = sys.argv[1:]
    if not args:
        usage()
        sys.exit(2)
    if '-h' in args or '--help' in args:
        usage()
        sys.exit(2)
    merge_results(args[:])


def merge_results(xml_files):
    errors = 0
    failures = 0
    skipped = 0
    tests = 0
    time = 0.0
    cases = []
    for file_name in xml_files:
        tree = ET.parse(file_name)
        test_suite = tree.getroot()
        errors += int(test_suite[0].attrib['errors'])
        failures += int(test_suite[0].attrib['failures'])
        skipped += int(test_suite[0].attrib['skipped'])
        tests += int(test_suite[0].attrib['tests'])
        time += float(test_suite[0].attrib['time'])
        cases.append(test_suite[0].getchildren())

    new_root = ET.Element('testsuites')
    new_testsuite = ET.Element('testsuite')
    new_testsuite.attrib['errors'] = '%s' % errors
    new_testsuite.attrib['failures'] = '%s' % failures
    new_testsuite.attrib['skipped'] = '%s' % skipped
    new_testsuite.attrib['tests'] = '%s' % tests
    new_testsuite.attrib['time'] = '%s' % time
    for case in cases:
        new_testsuite.extend(case)

    new_root.insert(0, new_testsuite)
    new_tree = ET.ElementTree(new_root)
    ET.dump(new_tree)


def usage():
    this_file = os.path.basename(__file__)
    print('Usage:  %s results1.xml results2.xml' % this_file)


if __name__ == '__main__':
    main()

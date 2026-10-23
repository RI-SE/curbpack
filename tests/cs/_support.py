"""Small output adapter for standalone stdlib unittest scripts; no third-party runner."""
import os
import sys
import unittest

def _status(word):
    if sys.stdout.isatty() and not os.environ.get("NO_COLOR"):
        color = "32" if word == "PASS" else "31" if word == "FAIL" else "33"
        return f"\033[{color}m[{word}]\033[0m"
    return f"[{word}]"

class _Result(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        self._name = test._testMethodName

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.writeln(f"{_status('PASS')} {self._name}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.writeln(f"{_status('FAIL')} {self._name}")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.writeln(f"{_status('FAIL')} {self._name} (unexpected exception)")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.stream.writeln(f"{_status('SKIP')} {self._name}: {reason}")

class _Runner(unittest.TextTestRunner):
    resultclass = _Result

def run():
    unittest.main(verbosity=0, testRunner=_Runner(stream=sys.stdout, verbosity=0))

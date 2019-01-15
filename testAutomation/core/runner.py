from time import time
from unittest.runner import TextTestRunner

from colour_runner.result import ColourTextTestResult
from django.test.runner import DiscoverRunner


class TimedColourTextTestResult(ColourTextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clocks = dict()
        self.test_timings = []

    def startTest(self, test):
        self.clocks[test] = time()
        super().startTest(test)

    def addSuccess(self, test):
        elapsed = (time() - self.clocks[test])
        self.test_timings.append((test, elapsed))
        super().addSuccess(test)

    def getTestTimings(self):
        return self.test_timings


class TimedColourTextTestRunner(TextTestRunner):
    resultclass = TimedColourTextTestResult

    def __init__(self, slow_test_threshold, **kwargs):
        self.slow_test_threshold = slow_test_threshold
        super().__init__(**kwargs)

    def run(self, test):
        result = super().run(test)

        timings = result.getTestTimings()
        timings.sort(key=lambda x: -1 * x[1])

        if timings and timings[0][1] > self.slow_test_threshold:
            self.stream.writeln(
                '\nSlow Tests (>{:.03}s):'.format(self.slow_test_threshold),
            )
            for test, elapsed in timings:
                if elapsed > self.slow_test_threshold:
                    test_class = result.getClassDescription(test)
                    name = result.getShortDescription(test)
                    self.stream.writeln(
                        '({:.04}s) {} ({})'.format(elapsed, name, test_class),
                    )

        return result


class TestRunner(DiscoverRunner):
    test_runner = TimedColourTextTestRunner

    def __init__(self, slow_test_threshold, **kwargs):
        self.slow_test_threshold = slow_test_threshold
        super().__init__(**kwargs)

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--slow-test-threshold', dest='slow_test_threshold', default=0.3, type=float,
            help='Tests that take longer than this threshold will be output.',
        )

    def get_test_runner_kwargs(self):
        kwargs = super().get_test_runner_kwargs()
        kwargs['slow_test_threshold'] = self.slow_test_threshold
        return kwargs

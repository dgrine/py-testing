################################################################################
# testing.application
#
# Copyright 2017. Djamel Grine.
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, 
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, 
#    this list of conditions and the following disclaimer in the documentation 
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
################################################################################
from base.application.log import initialize_logging, get_logger
from base.application.application import Application, arg
from base.py.modules import this_module_path_relative
from base.utilities.colors import bcolors, get_color_string
from testing.suite import build_test_suite, run_test_suite
import os
import re
from testing import TestCase

initialize_logging(
    name = 'testdriverapp',
    logger_descriptions = {
        'handler_type': 'StreamHandler',
        'level': 'info',
        'format': '%(message)s'
        }
   )
log = get_logger('testdriverapp')

class Application(Application):
    path = arg(
        'path',
        help = 'Top path used to search for unit-tests',
        type = str
       )
    includes_modules = arg(
        '--include-modules',
        nargs = '+',
        help = 'regex for unit-test modules to include',
        default = ['.*']
       )
    includes_classes = arg(
        '--include-classes',
        nargs = '+',
        help = 'regex for unit-test classes to include',
        default = ['.*']
       )
    includes_methods = arg(
        '--include-methods',
        nargs = '+',
        help = 'regex for unit-test methods to include',
        default = ['.*']
       )

    def __init__(self):
        super(Application, self).__init__()
        
        # Check that the path exists
        if not os.path.isdir(self.path):
            log.error("'%s' is not a directory", self.path)
            exit(1)

        # Create the selector
        class Selector(object):
            def __init__(self, includes_list):
                self.includes = includes_list

            def __call__(self, name):
                for expr in self.includes:
                    if None != re.match(expr, name): return True
                return False
        
        # Build the test suite
        self._suite, self._selection = build_test_suite(
            root_path = this_module_path_relative('..'),
            test_path = self.path,
            filter_modules = Selector(self.includes_modules),
            filter_classes = Selector(self.includes_classes),
            filter_methods = Selector(self.includes_methods)
           )
        
    def run(self):
        try:
            self._print_selection()

            log.info(
                get_color_string(bcolors.BOLD, "Running ".ljust(80, '='))
           )
            self._result = run_test_suite(self._suite)

            self._print_result()

        except KeyboardInterrupt:
            pass
            
    def _print_selection(self):
        log.info(
            get_color_string(bcolors.BOLD, "Unit-tests ".ljust(80, '='))
           )

        for _module_name in self._selection:
            log.info(
                get_color_string(bcolors.UNDERLINE, _module_name)
               )
            for _class_name in self._selection[_module_name]:
                log.info(
                    "  %s" % get_color_string(bcolors.WHITE, _class_name)
                   )
                for fnc in self._selection[_module_name][_class_name]:
                    log.info("    %s", get_color_string(bcolors.WHITE, fnc))

    def _print_result(self):
        log.info(
            get_color_string(bcolors.BOLD, "Results ".ljust(80, '='))
           )
        if self._result.wasSuccessful():
            msg = "STATUS: Success. All unit-tests passed."
            log.info(get_color_string(bcolors.GREEN, msg))
        else:
            msg = "STATUS: Failed. There were %d failures and %d "\
                    "unexpected errors.\n" % \
                    (
                        len(self._result.failures),
                        len(self._result.errors)
                   )
            log.error(get_color_string(bcolors.RED, msg))

            # Failures: test case test signals a failure
            for n, (testcase, traceback) in enumerate(self._result.failures):
                msg = "- Failure #%d: %s " % ((n + 1), testcase)
                log.error(
                    get_color_string(bcolors.RED, msg.ljust(80, '-'))
                   )
                log.error(traceback)

            # Errors: test case with unexpected error
            for n, (testcase, traceback) in enumerate(self._result.errors):
                msg = "- Error #%d: %s " % ((n + 1), testcase)
                log.critical(
                    get_color_string(bcolors.RED, msg.ljust(80, '-'))
                   )
                log.critical(traceback)

app = Application()


################################################################################
# testing.suite
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
from base.py.modules import \
    get_module_name_from_path, load_module, find_classes_in_module
from testing import TestCase
from functools import wraps
import os
import unittest

log = get_logger( 'testdriverapp' )

def _find_unittest_directories( path ):
    return [
        dirpath \
        for ( dirpath, dirnames, filenames ) in os.walk(
            path
            ) \
        if '_unittests' == os.path.split( dirpath )[ 1 ]
        ]

def _list_unittest_files( path ):
    return [
        os.path.join( path, file ) \
        for file in os.listdir( path )
        if file.startswith( 'test' )
        and file.endswith( '.py' )
        ]

def _get_test_modules( root_path, test_path ):
    testfolders = [
        os.path.join( folder, 'tests' )
        for folder in _find_unittest_directories( test_path )
        ]
    modules = []
    for testfolder in testfolders:
        for testfile in _list_unittest_files( testfolder ):
            module_name = get_module_name_from_path( root_path, testfile )
            log.noise( "Loading module %s", module_name )
            module = load_module( module_name )
            modules.append( module )
    return modules

def wrapped_test_function( test_method ):
    """
    Wraps a test method so that we can log which test case we're running.
    """
    @wraps( test_method )
    def wrapper( *args, **kwargs ):
        log.debug( "Running %s", test_method.__name__ )
        return test_method( *args, **kwargs )
    return wrapper

def build_test_suite( root_path, test_path, \
    filter_modules, filter_classes, filter_methods ):
    assert type( root_path ) in ( str, unicode ), \
        "Expected string type"
    assert type( test_path ) in ( str, unicode ), \
        "Expected string type"
    assert os.path.isdir( root_path ), \
        "'%s' is not a folder" % root_path
    assert os.path.isdir( test_path ), \
        "'%s' is not a folder" % test_path

    test_path = os.path.abspath( test_path )
    suite = unittest.TestSuite()
    selection = {}  # Dictionary that represents the selection tree
    for module in _get_test_modules( root_path, test_path):
        number_of_selected_test_functions_in_module = 0

        # Do we include this module?
        if not filter_modules( module.__name__ ): continue

        # Get the test classes in that module
        for cls in [ cls for cls in find_classes_in_module(
            module,
            filter = lambda name, value: \
                    issubclass( value, TestCase ) 
                        and not
                    TestCase == value
            )
            if filter_classes( cls.__name__ )
            ]:

            # Get the test functions available in that class
            all_methods = [
                fnc for fnc in dir( cls ) if fnc.startswith( 'test' )
                ]

            # Disable the methods as required
            # for fnc in disabled_methods: delattr( cls, fnc )
            for fnc in all_methods:
                if not filter_methods( fnc ):
                    delattr( cls, fnc )
                else:
                    # Substitute with a wrapped test function
                    setattr( cls, fnc, wrapped_test_function( getattr( cls, fnc ) ) )

            # Select the test functions
            # If no tests are selected, skip to the next class
            test_functions = [
                func for func in dir( cls ) if func.startswith( 'test' )
                ]
            if 0  == len( test_functions ): continue

            # List the test functions
            if not module.__name__ in selection: selection[ module.__name__ ] = {}
            selection[ module.__name__ ][ cls.__name__ ] = test_functions

            # Load the test case and add it to the suite
            cls_suite = unittest.TestLoader().loadTestsFromTestCase( cls )
            suite.addTest( cls_suite )
    return suite, selection

def run_test_suite( suite ):
    result = unittest.TestResult()
    suite.run( result )
    return result

# Copyright 2012 Arunjit Singh. All Rights Reserved.
"""Build definitions for CC builds using SCons. This script creates an SCons
environment and uses that to define libraries, binaries and tests. The tests
require the googletest framework, which is linked with each cc_test target.

There are two environment variables required:
* DEV_ROOT: The directory where all development is done. Should have directories
  'lib' and 'include' for library and include paths.
* GOOG: The directory that contains the 'googletest' directory.

Licence: MIT (http://www.opensource.org/licenses/mit-license.php).
Redistribution with or without modification must include this notice.
Author: Arunjit Singh <arunjit@me.com>
"""
import os

from SCons import Script

SYS_INCLUDES = ['/include', '/usr/include', '/usr/local/include']
SYS_LIBPATHS = ['/usr/lib', '/usr/local/lib']

DEV_ROOT = os.environ.get('DEV_ROOT')
AJ_INCLUDES = [os.path.join(DEV_ROOT, 'include'),
               os.path.join(DEV_ROOT, 'src')]
AJ_LIBPATHS = [os.path.join(DEV_ROOT, 'lib')]

COMMON_CCFLAGS = ['-Wall']
DEBUG_CCFLAGS = ['-g']
COMMON_CCLIBS = ['stdc++']

_current_srcs = ['../src'] if os.path.isdir('../src') else []
_current_libs = ['../build'] if os.path.isdir('../build') else []

INCLUDES = AJ_INCLUDES + _current_srcs + SYS_INCLUDES
LIBPATHS = AJ_LIBPATHS + _current_libs + SYS_LIBPATHS

_env = Script.Environment()
_env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = True

_env.Replace(CC='clang', CXX='clang++')


def _Uniq(lst):
  """Makes a list unique.

  Args:
    lst: (list) The list to make unique.

  Returns:
    A list with unique items in order.
  """
  seen = {}
  result = []
  for item in lst:
    item_id = id(item)
    if item_id not in seen:
      seen[item_id] = True
      result.append(item)
  return result


def _CreateTarget(target_type, target, source, CCFLAGS=None, CPPPATH=None,
                  LIBS=None, LIBPATH=None, debug=True, *args, **kwargs):
  """Creates a target.

  Args:
    target_type: (def) The type of target to make, ex: _env.Program.
    target: (str) The name of the target.
    source: (list) The source files.
  """
  assert type(source) is list
  if LIBS is None:
    LIBS = []
  if CCFLAGS is None:
    CCFLAGS = []
  if CPPPATH is None:
    CPPPATH = []
  if LIBPATH is None:
    LIBPATH = []

  ccflags = COMMON_CCFLAGS
  if debug:
    ccflags += DEBUG_CCFLAGS
  ccflags = _Uniq(ccflags + CCFLAGS)
  includes = _Uniq(INCLUDES + CPPPATH)
  libs = _Uniq(COMMON_CCLIBS + LIBS)
  libpaths = _Uniq(LIBPATHS + LIBPATH)
  return target_type(target=target,
                     source=source,
                     CCFLAGS=ccflags,
                     CPPPATH=includes,
                     LIBS=libs,
                     LIBPATH=libpaths,
                     *args,
                     **kwargs)


def cc_library(target, source, CCFLAGS=None, CPPPATH=None, LIBS=None,
               LIBPATH=None, debug=True, *args, **kwargs):
  """Creates a CC shared library target.

  Args:
    target: (str) The name of the target.
    source: (list) The source files.

  Returns:
    A SharedLibrary target.
  """
  return _CreateTarget(_env.SharedLibrary, target, source, CCFLAGS=CCFLAGS,
                       CPPPATH=CPPPATH, LIBS=LIBS, LIBPATH=LIBPATH, debug=debug,
                       *args, **kwargs)


def cc_binary(target, source, CCFLAGS=None, CPPPATH=None, LIBS=None,
              LIBPATH=None, debug=True, *args, **kwargs):
  """Creates a CC binary (Program) target.

  Args:
    target: (str) The name of the target.
    source: (list) The source files.

  Returns:
    A Program target.
  """
  return _CreateTarget(_env.Program, target, source, CCFLAGS=CCFLAGS,
                       CPPPATH=CPPPATH, LIBS=LIBS, LIBPATH=LIBPATH, debug=debug,
                       *args, **kwargs)

# Testing using googletest.
GOOG = os.environ.get('GOOG')
GTEST_DIR = os.path.join(GOOG, 'googletest')
GTEST_SRC = [os.path.join(GTEST_DIR, 'src', 'gtest-all.cc')]
GTEST_INC = [os.path.join(GTEST_DIR, 'include'), GTEST_DIR]

_gtest_lib = None

def _GetTestLib():
  return cc_library(target='gtest',
                    source=GTEST_SRC,
                    CPPPATH=GTEST_INC)


def cc_test(target, source, CCFLAGS=None, CPPPATH=None, LIBS=None, LIBPATH=None,
            debug=True):
  """Creates a CC test target. Testing uses googletest (gtest/gtest.h).

  The caller need not specify the gtest library as an include/lib. This method
  includes the "gtest-all.cc" source file, making all tests available.

  Args:
    target: (str) The name of the target.
    source: (list) The source files.

  Returns:
    A test target.
  """
  global _gtest_lib
  if _gtest_lib is None:
    _gtest_lib = _GetTestLib()
  assert type(source) is list
  source = _Uniq(source + [_gtest_lib])
  if CPPPATH is None:
    CPPPATH = []
  CPPPATH = _Uniq(CPPPATH + GTEST_INC)
  return cc_binary(target, source, CCFLAGS=CCFLAGS, CPPPATH=CPPPATH, LIBS=LIBS,
                   LIBPATH=LIBPATH, debug=debug)

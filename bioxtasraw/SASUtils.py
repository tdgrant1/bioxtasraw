"""
Created on March 17, 2020

@author: Jesse Hopkins

#******************************************************************************
# This file is part of RAW.
#
#    RAW is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RAW is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RAW.  If not, see <http://www.gnu.org/licenses/>.
#
#******************************************************************************

This file contains functions used in several places in the program that don't really
fit anywhere else.
"""

from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import object, range, map, zip
from io import open
import six
from six.moves import cPickle as pickle

from ctypes import c_uint32, c_void_p, POINTER, byref
import ctypes.util
import atexit
import platform
import copy
import os
import subprocess
import glob
import json
import numpy as np
import sys

try:
    import dbus
except Exception:
    pass

import pyFAI

#NOTE: SASUtils should never import another RAW module besides RAWGlobals, to avoid circular imports.
try:
    import RAWGlobals
except Exception:
    from . import RAWGlobals


def loadFileDefinitions():
    file_defs = {'hdf5' : {}}
    errors = []

    if os.path.exists(os.path.join(RAWGlobals.RAWDefinitionsDir, 'hdf5')):
        def_files = glob.glob(os.path.join(RAWGlobals.RAWDefinitionsDir, 'hdf5', '*'))
        for fname in def_files:
            try:
                with open(fname, 'r') as f:
                    settings = f.read()

                settings = dict(json.loads(settings))

                file_defs['hdf5'][os.path.splitext(os.path.basename(fname))[0]] = settings
            except Exception:
                errors.append(fname)

    return file_defs, errors

def get_det_list():

    extra_det_list = ['detector']

    final_dets = pyFAI.detectors.ALL_DETECTORS

    for key in extra_det_list:
        if key in final_dets:
            final_dets.pop(key)

    for key in copy.copy(list(final_dets.keys())):
        if '_' in key:
            reduced_key = ''.join(key.split('_'))
            if reduced_key in final_dets:
                final_dets.pop(reduced_key)

    det_list = list(final_dets.keys()) + [str('Other')]
    det_list = sorted(det_list, key=str.lower)

    return det_list


class SleepInhibit(object):
    def __init__(self):
        self.platform = platform.system()

        if self.platform == 'Darwin':
            self.sleep_inhibit = MacOSSleepInhibit()

        elif self.platform == 'Windows':
            self.sleep_inhibit = WindowsSleepInhibit()

        elif self.platform == 'Linux':
            self.sleep_inhibit = LinuxSleepInhibit()

        else:
            self.sleep_inhibit = None

        self.sleep_count = 0

    def on(self):
        if self.sleep_inhibit is not None:
            try:
                self.sleep_inhibit.on()
                self.sleep_count = self.sleep_count + 1
            except Exception:
                pass

    def off(self):
        if self.sleep_inhibit is not None:
            self.sleep_count = self.sleep_count - 1

            if self.sleep_count <= 0:
                try:
                    self.sleep_inhibit.off()
                except Exception:
                    pass

    def force_off(self):
        if self.sleep_inhibit is not None:
            try:
                self.sleep_inhibit.off()
            except Exception:
                pass

class MacOSSleepInhibit(object):
    """
    Code adapted from the python caffeine module here:
    https://github.com/jpn--/caffeine

    Used with permission under MIT license
    """

    def __init__(self):
        self.libIOKit = ctypes.cdll.LoadLibrary(ctypes.util.find_library('IOKit'))
        self.cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreFoundation'))
        self.libIOKit.IOPMAssertionCreateWithName.argtypes = [ c_void_p, c_uint32, c_void_p, POINTER(c_uint32) ]
        self.libIOKit.IOPMAssertionRelease.argtypes = [ c_uint32 ]
        self.cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int32]
        self.cf.CFStringCreateWithCString.restype = ctypes.c_void_p

        self.kCFStringEncodingUTF8 = 0x08000100
        self._kIOPMAssertionLevelOn = 255
        self._IOPMAssertionRelease = self.libIOKit.IOPMAssertionRelease
        self._assertion = None
        self.reason = "RAW running long process"

        self._assertID = c_uint32(0)
        self._errcode = None

        atexit.register(self.off)

    def _CFSTR(self, py_string):
        return self.cf.CFStringCreateWithCString(None, py_string.encode('utf-8'), self.kCFStringEncodingUTF8)

    def _IOPMAssertionCreateWithName(self, assert_name, assert_level, assert_msg):
        assertID = c_uint32(0)
        p_assert_name = self._CFSTR(assert_name)
        p_assert_msg = self._CFSTR(assert_msg)
        errcode = self.libIOKit.IOPMAssertionCreateWithName(p_assert_name,
            assert_level, p_assert_msg, byref(assertID))
        return (errcode, assertID)

    def _assertion_type(self, display):
        if display:
            return 'NoDisplaySleepAssertion'
        else:
            return "NoIdleSleepAssertion"

    def on(self, display=False):
        # Stop idle sleep
        a = self._assertion_type(display)
        # if a != self._assertion:
        #     self.off()
        if self._assertID.value ==0:
            self._errcode, self._assertID = self._IOPMAssertionCreateWithName(a,
        self._kIOPMAssertionLevelOn, self.reason)

    def off(self):
        self._errcode = self._IOPMAssertionRelease(self._assertID)
        self._assertID.value = 0


class WindowsSleepInhibit(object):
    """
    Prevent OS sleep/hibernate in windows; code from:
    https://github.com/h3llrais3r/Deluge-PreventSuspendPlus/blob/master/preventsuspendplus/core.py
    and
    https://trialstravails.blogspot.com/2017/03/preventing-windows-os-from-sleeping.html
    API documentation:
    https://msdn.microsoft.com/en-us/library/windows/desktop/aa373208(v=vs.85).aspx
    """

    def __init__(self):
        self.ES_CONTINUOUS = 0x80000000
        self.ES_SYSTEM_REQUIRED = 0x00000001

    def on(self):
        ctypes.windll.kernel32.SetThreadExecutionState(
            self.ES_CONTINUOUS | \
            self.ES_SYSTEM_REQUIRED)

    def off(self):
        ctypes.windll.kernel32.SetThreadExecutionState(
            self.ES_CONTINUOUS)

# For linux
class LinuxSleepInhibit(object):
    """
    Based on code from:
    https://github.com/h3llrais3r/Deluge-PreventSuspendPlus
    """
    def __init__(self):
        self.sleep_inhibitor = None
        self.get_inhibitor()

    def get_inhibitor(self):
        try:
            #Gnome session inhibitor
            self.sleep_inhibitor = GnomeSessionInhibitor()
            return
        except Exception:
            pass

        try:
            #Free desktop inhibitor
            self.sleep_inhibitor = DBusInhibitor('org.freedesktop.PowerManagement',
                '/org/freedesktop/PowerManagement/Inhibit',
                'org.freedesktop.PowerManagement.Inhibit')
            return
        except Exception:
            pass

        try:
            #Gnome inhibitor
            self.sleep_inhibitor = DBusInhibitor('org.gnome.PowerManager',
                '/org/gnome/PowerManager',
                'org.gnome.PowerManager')
            return
        except Exception:
            pass

    def on(self):
        if self.sleep_inhibitor is not None:
            self.sleep_inhibitor.inhibit()

    def off(self):
        if self.sleep_inhibitor is not None:
            self.sleep_inhibitor.uninhibit()

class DBusInhibitor:
    def __init__(self, name, path, interface, method=['Inhibit', 'UnInhibit']):
        self.name = name
        self.path = path
        self.interface_name = interface

        bus = dbus.SessionBus()
        devobj = bus.get_object(self.name, self.path)
        self.iface = dbus.Interface(devobj, self.interface_name)
        # Check we have the right attributes
        self._inhibit = getattr(self.iface, method[0])
        self._uninhibit = getattr(self.iface, method[1])

    def inhibit(self):
        self.cookie = self._inhibit('Bioxtas RAW', 'long_process')

    def uninhibit(self):
        self._uninhibit(self.cookie)


class GnomeSessionInhibitor(DBusInhibitor):
    TOPLEVEL_XID = 0
    INHIBIT_SUSPEND = 4

    def __init__(self):
        DBusInhibitor.__init__(self, 'org.gnome.SessionManager',
                               '/org/gnome/SessionManager',
                               'org.gnome.SessionManager',
                               ['Inhibit', 'Uninhibit'])

    def inhibit(self):
        self.cookie = self._inhibit('Bioxtas RAW',
                                    GnomeSessionInhibitor.TOPLEVEL_XID,
                                    'long_process',
                                    GnomeSessionInhibitor.INHIBIT_SUSPEND)


def findATSASDirectory():
    opsys= platform.system()

    if opsys== 'Darwin':
        dirs = glob.glob(os.path.expanduser('~/ATSAS*'))
        if len(dirs) > 0:
            try:
                versions = {}
                for item in dirs:
                    atsas_dir = os.path.split(item)[1]
                    version = atsas_dir.lstrip('ATSAS-')
                    versions[version] = item

                max_version = get_max_version(versions, True)

                default_path = versions[max_version]

            except Exception:
                default_path = dirs[0]

            default_path = os.path.join(default_path, 'bin')

        else:
            default_path = '/Applications/ATSAS/bin'

    elif opsys== 'Windows':
        dirs = glob.glob(os.path.expanduser('C:\\Program Files (x86)\\ATSAS*'))

        if len(dirs) > 0:
            try:
                versions = {}
                for item in dirs:
                    atsas_dir = os.path.split(item)[1]
                    version = atsas_dir.lstrip('ATSAS-')
                    versions[version] = item

                max_version = get_max_version(versions, False)

                default_path = versions[max_version]

            except Exception:
                default_path = dirs[0]

            default_path = os.path.join(default_path, 'bin')

        else:
            default_path = 'C:\\atsas\\bin'

    elif opsys== 'Linux':
        default_path = '~/atsas'
        default_path = os.path.expanduser(default_path)

        if os.path.exists(default_path):
            dirs = glob.glob(default_path+'/*')

            for item in dirs:
                if item.split('/')[-1].lower().startswith('atsas'):
                    default_path = item
                    break

            default_path = os.path.join(default_path, 'bin')

    is_path = os.path.exists(default_path)

    if is_path:
        return default_path

    if opsys == 'Windows':
        which = subprocess.Popen('where dammif', stdout=subprocess.PIPE,shell=True)
        output = which.communicate()

        atsas_path = output[0].strip()

    else:
        which = subprocess.Popen('which dammif', stdout=subprocess.PIPE,shell=True)
        output = which.communicate()

        atsas_path = output[0].strip()

    if isinstance(atsas_path, bytes):
        atsas_path = atsas_path.decode('utf-8')

    if atsas_path != '':
        return os.path.dirname(atsas_path)

    try:
        path = os.environ['PATH']
    except Exception:
        path = None

    if path is not None:
        if opsys == 'Windows':
            split_path = path.split(';')
        else:
            split_path = path.split(':')

        for item in split_path:
            if item.lower().find('atsas') > -1 and item.lower().find('bin') > -1:
                if os.path.exists(item):
                    return item

    try:
        atsas_path = os.environ['ATSAS']
    except Exception:
        atsas_path = None

    if atsas_path is not None:
        if atsas_path.lower().find('atsas') > -1:
            atsas_path = atsas_path.rstrip('\\')
            atsas_path = atsas_path.rstrip('/')
            if atsas_path.endswith('bin'):
                return atsas_path
            else:
                if os.path.exists(os.path.join(atsas_path, 'bin')):
                        return os.path.join(atsas_path, 'bin')

    return ''

def get_max_version(versions, use_sub_minor):
    if use_sub_minor:
        max_version = '0.0.0-0'
    else:
        max_version = '0.0.0'
    for version in versions:
        if int(max_version.split('.')[0]) < int(version.split('.')[0]):
            max_version = version

        if (int(max_version.split('.')[0]) == int(version.split('.')[0])
            and int(max_version.split('.')[1]) < int(version.split('.')[1])):
            max_version = version

        if (int(max_version.split('.')[0]) == int(version.split('.')[0])
            and int(max_version.split('.')[1]) == int(version.split('.')[1])
            and int(max_version.split('.')[2].split('-')[0]) < int(version.split('.')[2].split('-')[0])):
            max_version = version

        if use_sub_minor:
            if (int(max_version.split('.')[0]) == int(version.split('.')[0])
                and int(max_version.split('.')[1]) == int(version.split('.')[1])
                and int(max_version.split('.')[2].split('-')[0]) == int(version.split('.')[2].split('-')[0])
                and int(max_version.split('-')[1]) < int(version.split('-')[1])):
                max_version = version

    return max_version


#This class goes with write header, and was lifted from:
#https://stackoverflow.com/questions/27050108/convert-numpy-type-to-python/27050186#27050186
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)

def find_global(module, name):
    if module == 'SASImage':
        module = 'SASMask'

        if name == 'RectangleMask':
            name = '_oldMask'
        elif name == 'CircleMask':
            name = '_oldMask'
        elif name == 'PolygonMask':
            name = '_oldMask'

    __import__(module)
    mod = sys.modules[module]

    klass = getattr(mod, name)
    return klass

if six.PY3:
    class SafeUnpickler(pickle.Unpickler):
        find_class = staticmethod(find_global)
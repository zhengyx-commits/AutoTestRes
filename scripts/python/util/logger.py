#!/usr/bin/env python
#
# Copyright 2018-2020 Amlogic.com, Inc. or its affiliates. All rights reserved.
#
# AMLOGIC PROPRIETARY/CONFIDENTIAL
#
# You may not use this file except in compliance with the terms and conditions
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
# DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
# IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
#
from past.builtins import basestring
from past.utils import old_div
import csv
import math
import sys
# if not 'sphinx' in sys.modules:
#     import numpy
import logging
from contextlib import contextmanager


class LTPLogger(object):
    """
    Class that provides methods for logging in the LTP format.
    """
    PASS = 'PASS'
    FAIL = 'FAIL'
    WARN = 'WARN'
    INFO = 'INFO'
    DEBUG = 'DEBUG'
    SKIP = 'CONF'
    BROK = 'BROK'
    PERF = 'PERF'

    @classmethod
    def format_value(cls, unit, value):
        """
        Format the given value based on the unit type
        """
        if isinstance(value, basestring):
            # strings don't need to be formatted
            return value
        elif unit == 's':
            # format seconds to 3 decimal points
            if isinstance(value, float):
                return '%.3f' % value
        elif unit == 'MB/s':
            if isinstance(value, float):
                return '%.2f' % value
        # generic format for anything that isn't handled above
        return repr(value)

    def __init__(self, name, log=None):
        if not log:
            log = self.create_logger()
        self.log = log
        self.name = name
        self.count = 0
        self.perf_data = {}

    @classmethod
    def create_logger(cls):
        """
        Create logger.
        """
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        log_format = "%(asctime)s [%(levelname)7s] %(message)s"
        log_date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(log_format, datefmt=log_date_format)
        handler.setFormatter(formatter)
        log = logging.Logger('')
        log.addHandler(handler)
        return log

    def log_info(self, msg, case_name=None):
        """
        Log an info message, does not increase instance count.
        """
        self._write_result(case_name, self.INFO, msg)

    def log_debug(self, msg, case_name=None):
        """
        Log a debug message, does not increases instance count.
        """
        self._write_result(case_name, self.DEBUG, msg)

    def log_warn(self, msg, case_name=None):
        """
        Log a warning message, does not increase instance count.
        """
        self._write_result(case_name, self.WARN, msg)

    def log_skip(self, msg, case_name=None):
        """
        Log a skip message, increases the instance count. Does not skip the
        test execution, use pytest.skip instead
        """
        self.log_auto_pass = False
        self._write_result(case_name, self.SKIP, msg, increase_count=False)

    def log_brok(self, msg, case_name=None):
        """
        Log a brok message, increases the instance count. Does not skip the
        test execution, use pytest.skip instead
        """
        self.log_auto_pass = False
        self._write_result(case_name, self.BROK, msg, increase_count=True)

    def log_pass(self, msg, case_name=None):
        """
        Log a pass message, increases the instance count.
        """
        self.log_auto_pass = False
        self._write_result(case_name, self.PASS, msg, increase_count=True)

    def log_fail(self, msg, case_name=None):
        """
        Log a fail message, increases instance count.
        """
        self.log_auto_pass = False
        self._write_result(case_name, self.FAIL, msg, increase_count=True)

    @contextmanager
    def trap_exception(self, msg=None, level=FAIL, type=Exception):
        """
        Trap exception and log it without raising further.
        """
        try:
            yield
        except Exception as e:
            if not isinstance(e, type):
                raise
            self._write_result(None, level, msg or str(e), increase_count=True)
            if level == self.BROK:
                raise

    # Perf data related
    def log_perf(self, name, unit, val, tp50=None, tp90=None,
                 minval=None, minindex=None, maxval=None, maxindex=None,
                 n=None, stddev=None):
        "Log a performance result message."
        parts = ['%s(%s) ' % (name, unit)]
        if minval and maxval:
            parts.append('avg=' + self.format_value(unit, val))
            if tp50 and tp90:
                parts.append(', tp50=' + self.format_value(unit, tp50))
                parts.append(', tp90=' + self.format_value(unit, tp90))
            parts.append(', min=' + self.format_value(unit, minval))
            parts.append(', min_i=' + self.format_value(unit, repr(minindex)))
            parts.append(', max=' + self.format_value(unit, maxval))
            parts.append(', max_i=' + self.format_value(unit, repr(maxindex)))
            if n:
                parts.append(', n=%s' % n)
            if stddev:
                parts.append(', stddev=%s' % stddev)
        else:
            parts.append(self.format_value(unit, val))

        self._write_result(None, result=self.PERF, msg=''.join(parts))

    def log_data(self, name, unit, data):
        "Log data."
        msg = 'DATA: %s(%s) [%s]' % (
                        name, unit,
                        ','.join([self.format_value(unit, v) for v in data]))
        self._write_result(None, result=self.INFO, msg=msg)

    def log_series_data(self, series, unit, data_only=False):
        "Log the specified data series"
        ds = self.get_series_data(series)
        # log the whole series
        self.log_data(name=series, unit=unit, data=ds)
        if data_only:
            return

        # log avg, tp50, tp90, min, max, stddev
        avg = '%.3f' % (sum(ds) / float(len(ds)))
        # tp50 = '%.3f' % numpy.percentile(ds, 50)
        # tp90 = '%.3f' % numpy.percentile(ds, 90)
        min_v = min(ds)
        max_v = max(ds)
        min_i = ds.index(min_v) + 1
        max_i = ds.index(max_v) + 1
        # stddev = '%.3f' % numpy.std(ds)

        self.log_perf(name=series, unit=unit, val=avg, tp50=tp50, tp90=tp90,
                      minval=min_v, minindex=min_i, maxval=max_v,
                      maxindex=max_i, n=len(ds), stddev=stddev)

    def add_series_data(self, series, value):
        "Add a data value to the given data series"
        if not series in self.perf_data:
            self.perf_data[series] = [value, ]
        else:
            self.perf_data[series].append(value)

    def get_series_data(self, series):
        "Get the specified data series"
        return self.perf_data[series]

    def get_series_avg(self, series):
        "Calculate the average for the specified series"
        ds = self.perf_data[series]
        return old_div(sum(ds), len(ds))

    def set_name(self, name):
        "Set the logger's name"
        self.name = name

    def get_name(self):
        "Get the logger's name"
        return self.name

    def clear_perf_data(self):
        "Clear all existing data"
        self.perf_data = {}

    def dump_series_data_to_csv(self,
                                outpath,
                                series,
                                unit,
                                file_mode='a',
                                log_units=False):
        ds = self.get_series_data(series)
        if log_units:
            data = ["{}({})".format(series, unit)]
        else:
            data = [series]
        for d in ds:
            data.append(self.format_value(unit, d))

        # by default mode, this function will append data to the output file
        with open(outpath, file_mode) as f:
            wr = csv.writer(f)
            wr.writerow(data)

    # Helper functions
    def _write_result(self, case_name, result, msg, increase_count=False):
        """
        Log a result for the test case.
        If increase_count = True, the instance count is incremented.
        """
        name = case_name or self.name
        msg = '%s\t%d  %s  :  %s' % (name, self.count, result, msg)
        if increase_count:
            self.count += 1

        if result == self.FAIL or result == self.BROK:
            self.log.error(msg)
        elif result == self.WARN:
            self.log.warning(msg)
        else:
            self.log.info(msg)
        logging.debug(msg)

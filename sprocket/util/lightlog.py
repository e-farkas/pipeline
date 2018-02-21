"""
a minimal lightweight logger (note: need manual handling)
"""
import time

import sprocket.util.joblog_pb2 as joblog_pb2

_logger_dict = {}


class Logger(object):
    def __init__(self):
        self.cached = []
        self.metadata = ''

    def debug(self, **kwargs):
        if 'ts' not in kwargs:
            kwargs['ts'] = time.time() # at least we know the time ...
        self.cached.append(kwargs)

    info = warning = error = debug

    def add_metadata(self, meta):
        self.metadata += meta

    def serialize(self):
        log = joblog_pb2.JobLog()
        for l in self.cached:
            r = log.record.add()
            for k,v in l.iteritems():
                setattr(r, k, v)
        log.metadata = self.metadata
        return log.SerializeToString()


def getLogger(logger):
    l = _logger_dict.get(logger, Logger())
    _logger_dict[logger] = l
    return l


#!/usr/bin/python
import logging

import libmu.util
from libmu import tracker, TerminalState, CommandListState, ForLoopState, OnePassState, ErrorState
from stages.util import default_trace_func


class FinalState(TerminalState):
    extra = "(finished)"


class EmitState(CommandListState):
    extra = "(emit output)"
    nextState = FinalState
    commandlist = [ (None, "quit:")
                  ]

    def __init__(self, prevState):
        super(EmitState, self).__init__(prevState, trace_func=default_trace_func)
        out_queue = prevState.out_queue
        out_key = prevState.out_key

        out_event = {'key': out_key}
        out_queue['frames'].put({'lineage': self.in_events['lineage'], 'frames': out_event, 'pipe_id': self.in_events['pipe_id']})


class RunState(CommandListState):
    extra = "(run)"
    nextState = EmitState
    commandlist = [ (None, 'run:mkdir -p ##TMPDIR##/out_0/')
                  , ('OK:RETVAL(0)', 'run:./ffmpeg -y -ss {starttime} -t {duration} -i "{URL}" -f image2 -c:v png -r 24 '
                                    '-start_number 1 ##TMPDIR##/out_0/%08d.png')
                  , ('OK:RETVAL(0)', 'emit:##TMPDIR##/out_0 {out_key}')
                  , ('OK:EMIT', None)
                    ]

    def __init__(self, prevState):
        super(RunState, self).__init__(prevState, trace_func=default_trace_func)
        self.out_queue = prevState.out_queue
        self.out_key = prevState.out_key

        params = {'starttime': self.in_events['video_url']['starttime'], 'duration': self.in_events['video_url']['duration'],
                  'URL': self.in_events['video_url']['key'], 'out_key': self.out_key}
        logging.debug('params: '+str(params))
        self.commands = [ s.format(**params) if s is not None else None for s in self.commands ]


class InitState(CommandListState):
    extra = "(init)"
    nextState = RunState
    commandlist = [ ("OK:HELLO", "seti:nonblock:0")
                  , "run:rm -rf /tmp/*"
                  , "run:mkdir -p ##TMPDIR##"
                  , None
                  ]

    def __init__(self, prevState, in_events, out_queue):
        super(InitState, self).__init__(prevState, in_events=in_events, trace_func=default_trace_func)
        self.out_queue = out_queue
        self.out_key = 's3://lixiang-pipeline/'+in_events['pipe_id']+'/decode/'+libmu.util.rand_str(16)+'/'
        logging.debug('in_events: '+str(in_events)+', out_queue: '+str(out_queue))

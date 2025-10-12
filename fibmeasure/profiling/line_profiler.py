from threading import Lock
from typing import Callable

from line_profiler.line_profiler import LineProfiler, show_text


class classproperty:
    def __init__(self, func):
        self.fget = func

    def __get__(self, instance, owner):
        return self.fget(owner)


class SingletonMeta(type):
    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class Logs:
    def __init__(self, profile_string: str = None):
        if profile_string is None:
            self.profile_string = ''
        elif isinstance(profile_string, str):
            self.profile_string = profile_string
        else:
            raise TypeError(f'profile_string must be a string, got {type(profile_string)}')

    def __repr__(self):
        return self.profile_string

    def write(self, str: str):
        self.profile_string = self.profile_string + str


class ProfilerOutputs(metaclass=SingletonMeta):
    def __init__(self):
        self.__logs = {}

    def __call__(self, funcname: str, profiling_id: int):
        if funcname in self.__logs:
            self.__logs[funcname].append(profiling_id)
        else:
            self.__logs[funcname] = [
                profiling_id,
            ]

    def __repr__(self):
        if len(self.__logs) == 0:
            return 'ProfilerOutputs(empty)'
        else:
            format_str = '\n'
            nlogs = 0
            for funcname, logs in self.__logs.items():
                format_str += '    function ' + funcname + f' with {len(logs)} logs\n'
                nlogs += len(logs)
            return f'ProfilerOutputs({format_str}), totaly of {nlogs} entries'

    def __getitem__(self, funcname: str) -> str | list[str]:
        def get_log(profiling_id):
            logs = Logs()
            stats = LProfiler.get_master_profiler().get_stats()
            metadata = list(stats.timings.items())[profiling_id]
            metadata = {metadata[0]: metadata[1]}
            unit = stats.unit
            show_text(metadata, unit, stream=logs)
            return logs

        output = [get_log(profiling_id) for profiling_id in self.__logs[funcname]]
        if len(output) == 1:
            return output[0]
        return output

    def reset(self):
        self.__logs = {}


class OutputHandler:
    def __getattr__(self, attr):
        return ProfilerOutputs()[attr]

    def __repr__(self):
        return ProfilerOutputs().__repr__()


class LProfiler:
    __master_profiler = LineProfiler()
    __func_bindings = {}

    @classmethod
    def get_master_profiler(cls):
        return cls.__master_profiler

    @classmethod
    def profile(cls, function: Callable):
        profiler = cls.__master_profiler
        profiler_outputs = ProfilerOutputs()
        cls.__func_bindings[function] = profiler(function)
        funcname = function.__name__

        profiling_id = len(profiler.get_stats().timings) - 1

        profiler_outputs(funcname, profiling_id)

        def wrapped(*args, **kwargs):
            wrapped_func = cls.__func_bindings[function]
            return wrapped_func(*args, **kwargs)

        return wrapped

    @classmethod
    def reset(cls):
        profiler_outputs = ProfilerOutputs()
        profiler_outputs.reset()
        cls.__master_profiler = LineProfiler()
        profiler = cls.__master_profiler
        for function in cls.__func_bindings:
            cls.__func_bindings[function] = profiler(function)
            funcname = function.__name__
            profiling_id = len(profiler.get_stats().timings) - 1
            profiler_outputs(funcname, profiling_id)

    @classproperty
    def output(cls):
        return OutputHandler()

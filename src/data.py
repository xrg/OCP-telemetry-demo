#!/bin/env python3

from __future__ import annotations

import logging
import time
from threading import Thread
from typing import Any, NamedTuple, Type, Union
from random import SystemRandom

logger = logging.getLogger(__name__)

rnd = SystemRandom()

class Sample(NamedTuple):
    timestamp: Union[int, float]
    value: Any

class FloatSample(Sample):
    value: float

    @classmethod
    def sample(cls, tcur:float, vmin: float, vmax: float):
        value = (rnd.random() * (vmax - vmin)) + vmin
        return cls(timestamp=tcur, value=round(value, 5))


class Meter(NamedTuple):
    """Definition of one property to be measured
    """
    path: str
    sample_cls: Type[Sample]
    update_sec: float = 1.0
    vmin: float = 0.0
    vmax: float = 1.0


class SampleGen:
    """holds the state of some meter on a host"""
    def __init__(self, tseries: list, meter: Meter):
        self._meter = meter
        self._tseries = tseries
        self.tnext = 0.0

    def tick(self, tcur: float):
        """Creates one sample, adds to series, returns next timestamp
        """
        m = self._meter
        self._tseries.append(m.sample_cls.sample(tcur, m.vmin, m.vmax))
        if self._meter.update_sec > 0.0:
            self.tnext = tcur + self._meter.update_sec
        else:
            raise NotImplementedError("non-positive update")


all_hosts = {}

meters_def = [
    Meter(path="/power/watts", sample_cls=FloatSample, vmin=5.0, vmax=400.0),
    ]

class DataThread(Thread):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pending = []

    def _gen_hostnames(self):
        """Generate a range of hostnames"""
        for prefix in "abc", "def", "ghi":
            for num in range(10):
                yield f"{prefix}{num:03d}.example.com"

    def _init_hosts(self):
        for hostname in self._gen_hostnames():
            host_vals = {}
            for meter in meters_def:
                values = []
                host_vals[meter.path] = values
                self._pending.append(SampleGen(values, meter))

            all_hosts[hostname] = host_vals

    def run(self):
        global all_hosts
        logger.info("initializing data")
        tcur = round(time.time() - 100, 3)

        self._init_hosts()
        try:
            while True:
                tnext = tcur + 1.0
                for pend in self._pending:
                    if pend.tnext > tcur:
                        continue

                    pend.tick(tcur)

                tnext = max(p.tnext for p in self._pending)
                tcur = max(tnext, tcur + 0.001)

                if tcur > time.time():
                    time.sleep(tcur - time.time())
        except KeyboardInterrupt:
            pass


_data_thread = None

def data_startup():
    global _data_thread
    if _data_thread is not None:
        raise RuntimeError("Already there")
    _data_thread = DataThread()
    _data_thread.daemon = True
    _data_thread.start()
    logger.info("Started data thread")

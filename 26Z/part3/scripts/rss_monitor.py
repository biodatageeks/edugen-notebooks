"""Sample a worker's current RSS from a separate process during one operation.

The sampler does not share the worker's GIL. It stops before validation reads the
result. Unlike ru_maxrss, this metric cannot carry a pre-exec memory high-water
mark from the notebook process. Sampling may miss peaks shorter than 10 ms.
"""
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

INTERVAL = 0.01


class RssMonitor:
    def __enter__(self):
        self.process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), str(os.getpid())],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        )
        try:
            message = json.loads(self.process.stdout.readline())
            if message.get('status') != 'ready':
                raise RuntimeError('Monitor RSS nie potwierdził gotowości.')
        except BaseException:
            self.process.kill()
            self.process.communicate()
            raise
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            output, error = self.process.communicate('stop\n', timeout=10)
            if self.process.returncode:
                raise RuntimeError('Monitor RSS: ' + error[-2000:])
            self.result = json.loads(output)
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.communicate()


def watch(pid):
    import psutil
    worker = psutil.Process(pid)
    baseline = peak = worker.memory_info().rss
    samples = 1
    previous = time.perf_counter()
    max_gap = 0.0
    print(json.dumps({'status': 'ready'}), flush=True)
    while True:
        ready, _, _ = select.select([sys.stdin], [], [], INTERVAL)
        now = time.perf_counter()
        max_gap = max(max_gap, now - previous)
        previous = now
        peak = max(peak, worker.memory_info().rss)
        samples += 1
        if ready:
            # EOF also stops the sampler if its worker exits unexpectedly.
            sys.stdin.readline()
            break
    print(json.dumps({
        'peak_rss_gib': peak / 2**30,
        'rss_start_gib': baseline / 2**30,
        'rss_method': 'sampled_current_rss_during_query',
        'rss_sample_interval_seconds': INTERVAL,
        'rss_samples': samples,
        'rss_max_sample_gap_seconds': max_gap,
    }), flush=True)


if __name__ == '__main__':
    watch(int(sys.argv[1]))

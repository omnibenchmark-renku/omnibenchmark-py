import json
import os

import requests

from omnibenchmark.utils.local_cache.config import local_bench_cat_data, init_dirs
from omnibenchmark.utils.default_global_vars import BENCH_URL


def download_orchestrator_data(force: bool = False, bench_url: str = BENCH_URL):
    if force or not os.path.isfile(local_bench_cat_data):
        r = requests.get(bench_url)
        data = r.json()
        with open(local_bench_cat_data, 'w') as f:
            json.dump(data, f)

def init_local_cache(bench_url: str = BENCH_URL):
        init_dirs()
        download_orchestrator_data(bench_url = bench_url)

def update_local_cache(bench_url: str = BENCH_URL):
    download_orchestrator_data(force=True, bench_url = bench_url)
    # do we want to include other sources into local cache?
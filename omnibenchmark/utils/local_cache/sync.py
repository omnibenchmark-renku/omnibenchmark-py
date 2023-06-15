import json
import os

import requests

from omnibenchmark.utils.local_cache.config import local_bench_cat_data, init_dirs

git_url = "https://raw.githubusercontent.com/"
omni_essentials = "omnibenchmark/omni_essentials/"
cat_json = "main/general/benchmark_categories.json?inline=false"

bench_cat_url = git_url + omni_essentials + cat_json

def download_orchestrator_data(force: bool = False, bench_url: str = bench_cat_url):
    if force or not os.path.isfile(local_bench_cat_data):
        r = requests.get(bench_url)
        data = r.json()
        with open(local_bench_cat_data, 'w') as f:
            json.dump(data, f)

def init_local_cache(bench_url: str = bench_cat_url):
        init_dirs()
        download_orchestrator_data(bench_url = bench_url)

def update_local_cache(bench_url: str = bench_cat_url):
    download_orchestrator_data(force=True, bench_url = bench_url)
    # do we want to include other sources into local cache?
import json
import os

import requests

from .config import local_bench_cat_data

git_url = "https://renkulab.io/gitlab/"
omni_essentials = "omnibenchmark/omni_essentials/"
cat_json = "-/raw/master/general/benchmark_categories.json?inline=false"

bench_cat_url = git_url + omni_essentials + cat_json

def download_orchestrator_data(force=False, bench_cat_url: str = bench_cat_url):
    if force or not os.path.isfile(local_bench_cat_data):
        r = requests.get(bench_cat_url)
        data = r.json()
        with open(local_bench_cat_data, 'w') as f:
            json.dump(data, f)
import os

_home = os.path.expanduser('~')

app_name = "omnibenchmark-py"

xdg_data_home = os.environ.get('XDG_DATA_HOME') or \
            os.path.join(_home, '.local', 'share')

data_dir = os.path.join(xdg_data_home, app_name)
local_bench_cat_data = os.path.join(data_dir, "benchmark_categories.json")

def init_dirs():
    os.makedirs(data_dir, exist_ok=True)

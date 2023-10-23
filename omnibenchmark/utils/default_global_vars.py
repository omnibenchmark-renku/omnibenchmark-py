"""Default settings"""


from renku.api import Project
from renku.core.util.git import get_remote, parse_git_url

remote_url = get_remote(Project().repository).url
remote_git = parse_git_url(remote_url)

KG_URL = "https://renkulab.io/knowledge-graph"
DATA_URL = KG_URL + "/datasets/"
DATA_QUERY_URL = KG_URL + "/entities?query="
GIT_URL =  remote_git.scheme + "://" + remote_git.hostname
ESS_URL = "https://raw.githubusercontent.com/omnibenchmark/omni_essentials/"
BENCH_URL = ESS_URL + "main/general/benchmark_categories.json?inline=false"
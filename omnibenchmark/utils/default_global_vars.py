"""Default settings - overwrite locally"""


class OmniRenkuInst(object):
    """Class to store the omnibenchmark renku configuration"""

    KG_URL = "https://renkulab.io/knowledge-graph"
    DATA_URL = KG_URL + "/datasets/"
    DATA_QUERY_URL = KG_URL + "/entities?query="
    RENKU_URL = "https://renkulab.io"
    GIT_URL = "https://gitlab.renkulab.io"
    GRAPHQL_URL = "https://renkulab.io/knowledge-graph/graphql"
    GIT_API = "https://renkulab.io/gitlab/api/v4/"
    ESS_URL = "https://raw.githubusercontent.com/omnibenchmark/omni_essentials/"
    BENCH_URL = ESS_URL + "main/general/benchmark_categories.json?inline=false"

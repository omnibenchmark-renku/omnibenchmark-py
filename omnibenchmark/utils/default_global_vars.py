"""Default settings - overwrite locally"""


class OmniRenkuInst(object):
    """Class to store the omnibenchmark renku configuration"""

    KG_URL = "https://renkulab.io/knowledge-graph"
    DATA_URL = KG_URL + "/datasets/"
    DATA_QUERY_URL = KG_URL + "/datasets?query="
    RENKU_URL = "https://renkulab.io"
    GIT_URL = "https://renkulab.io/gitlab"
    GRAPHQL_URL = "https://renkulab.io/knowledge-graph/graphql"
    GIT_API = "https://renkulab.io/gitlab/api/v4/"
    BENCH_URL = "https://omnibenchmark.pages.uzh.ch/omni_dash/benchmarks"

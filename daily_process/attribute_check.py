"""
  Script to run to map Jira IDs (ISCA#) to names of isssues
  typically, this is a gene symbol, but it may also be a region.
  Only pulling tickets for type=Gene Curation Only

  Write index to /net/web/public/htdocs/projects/dbvar/clingen
  cron this to run daily.

  This will produce two output files:
    gene_isca.idx: gene to ISCA-# file for web cgi to read
    gene_id_isca: list of gene IDs in Jira, use to update gene symbol/alias index
       can also use this to update Jira with new gene symbols, etc. (different script)

  Need to run under the web account so you can have a private password file
"""

import os
import sys
import isca_me_util

# config file
DATA_DIR = '../conf'
CONFIG = os.path.join(DATA_DIR, '.isca_config')
if __name__ == "__main__":

    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    query_str = ('project = ISCA AND issuetype in '
                 '(\"ISCA Gene Curation\", \"ISCA Region Curation\") '
                 'AND resolution = Unresolved AND \"GRCh37 SeqID\" is empty ')
    issue_list = isca_me_util.GetIssuesByJQL(jira, query_str, sys.stdout)

    for issue in issue_list:
        print("invalid value for field GRCh37 SeqID for ticket " + issue.key, file=sys.stderr)

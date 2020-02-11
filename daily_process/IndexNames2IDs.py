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
STD_FIELD_FILE = os.path.join(DATA_DIR, 'standard_field.ini')

FILTER_ID = 10633

if __name__ == "__main__":
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')
    issue_list = isca_me_util.GetIssuesByJQL(jira, 'filter=' + str(FILTER_ID), sys.stdout)

    designated_fields = ['Gene Symbol', 'Link to Gene', 'Status', 'Resolution']
    FH_OUT1 = open('gene_isca.idx', 'w')
    FH_OUT2 = open('gene_id.idx', 'w')
    for issue in issue_list:

        # gene_symbol
        try:
            value_dict = isca_me_util.IssueEntries(issue, ISCA_dict, designated_fields)
            gene_symbol = value_dict['Gene Symbol']
            gene_id = value_dict['Link to Gene'].split('/')[-1]
            status = value_dict['Status']
            resolution = value_dict['Resolution']
            if (not gene_symbol) or (not gene_id):
                print("invalid empty value of Gene Symbol or Gene ID for ticket " + issue.key,
                      file=sys.stderr)
                continue
            if status == 'Closed' and resolution == "Duplicate":
                continue
        except Exception as err:
            print("Error in get gene_symbol or id for {} as {}".format(issue.key, str(err)),
                  file=sys.stderr)
            continue

        print("%s\t%s" % (gene_symbol, issue.key), file=FH_OUT1)
        print("%s\t%s" % (issue.key, gene_id), file=FH_OUT2)

    FH_OUT1.close()
    FH_OUT2.close()

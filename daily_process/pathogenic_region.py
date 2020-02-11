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
REGION_OUT_HTML = "pathogenic_region_body.html"

if __name__ == "__main__":

    gene_symbol_hash = {}
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')
    query_str = ('project = ISCA AND issuetype in (\"ISCA Region Curation\") '
                 'AND labels in (\"nstd45pathogenic\") ')
    issue_list = isca_me_util.GetIssuesByJQL(jira, query_str, sys.stdout)
    designated_fields = [
                          'ISCA Region Name',
                          'ISCA Haploinsufficiency score',
                          'ISCA Triplosensitivity score',
                          'GRCh37 Genome Position',
                          'Components',
                          'Status',
                          'Resolution']

    FH_HTML = open(REGION_OUT_HTML, 'w')
    for issue in issue_list:
        try:
            value_dict = isca_me_util.IssueEntries(issue, ISCA_dict, designated_fields)
            region_name = value_dict['ISCA Region Name']
            gain_score = value_dict['ISCA Triplosensitivity score']
            loss_score = value_dict['ISCA Haploinsufficiency score']
            genome_pos = value_dict['GRCh37 Genome Position']
            component = value_dict['Components']
            status = value_dict['Status']
            resolution = value_dict['Resolution']

            display_status = ""
            if status == 'Closed' and resolution == 'Complete':
                display_status = ""
            elif status == 'Closed' and resolution == "Won't Fix":
                display_status = 'patho_region_remove'
            elif status == 'Closed' and resolution == "Duplicate":
                display_status = 'patho_region_duplicate'
            elif status == 'Open':
                display_status = 'patho_region_open'
            else:
                display_status = 'patho_region_underreview'

            genome_pos = genome_pos.replace(",", "").replace(" ", "")
            if display_status != "":
                print("\t<tr class=\"%s\">" % (display_status), file=FH_HTML)
            else:
                print("\t<tr>", file=FH_HTML)

            print(("\t<td><a href=\"clingen_region.cgi?id=%s\" target=\"_blank\">%s"
                   "</a></td>") % (issue.key, region_name), file=FH_HTML)
            print("\t<td>%s</td>" % (genome_pos), file=FH_HTML)
            print("\t<td>%s</td>" % (loss_score), file=FH_HTML)
            print("\t<td>%s</td>\n\t</tr>" % (gain_score), file=FH_HTML)
            # print >>FH_HTML, "\t<td>%s</td>" %(",".join(issue.fields.labels))
            # print >>FH_HTML, "\t<td>%s</td>\n\t</tr>" %(component)

        except Exception as err:
            print("Error in for " + issue.key + " as " + str(err), file=sys.stderr)
            continue

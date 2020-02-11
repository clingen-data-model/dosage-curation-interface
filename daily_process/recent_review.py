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
RECENT_REVIEW_HTML = "recent_review.html"

if __name__ == "__main__":

    gene_symbol_hash = {}
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')
    issue_list = isca_me_util.GetIssuesByJQL(jira, 'filter=13642 ORDER BY updated DESC',
                                             sys.stdout)

    FH_HTML = open(RECENT_REVIEW_HTML, 'w')
    print("<h3>Genes/Regions Recently Reviewed</h3>", file=FH_HTML)
    print("<table data-jig=\"ncbigrid\">", file=FH_HTML)
    print("\t<thead>\n\t<tr>", file=FH_HTML)
    print("\t<th>Gene/Region name</th>", file=FH_HTML)
    print("\t<th class=\"score_col\">Haploinsufficiency score</th>", file=FH_HTML)
    print("\t<th class=\"score_col\">Triplosensitivity score</th>", file=FH_HTML)
    print("\t<th>Date reviewed</th>", file=FH_HTML)
    print("\t</tr>\n\t</thead>", file=FH_HTML)
    print("\t<tbody>", file=FH_HTML)

    for issue in issue_list:
        try:
            name, href_prefix = '', ''
            issue_type = getattr(issue.fields, ISCA_dict['Type']).name.strip()
            if issue_type == 'ISCA Gene Curation':
                name = getattr(issue.fields, ISCA_dict['Gene Symbol']).strip()
                href_prefix = 'clingen_gene.cgi?sym=' + name
            elif issue_type == 'ISCA Region Curation':
                name = getattr(issue.fields, ISCA_dict['ISCA Region Name']).strip()
                href_prefix = 'clingen_region.cgi?id=' + issue.key
            else:
                continue

            loss_score = getattr(issue.fields, ISCA_dict['ISCA Haploinsufficiency score']).value
            gain_score = getattr(issue.fields, ISCA_dict['ISCA Triplosensitivity score']).value
            resolutiondate = getattr(issue.fields, ISCA_dict['Resolved']).split('T')[0].strip()

            print("\t<tr>\n\t<td><a href=\"%s\" target=\"_blank\">%s</a></td>" % (
                href_prefix, name), file=FH_HTML)
            print("\t<td class=\"score_col\">%s</td>" % (loss_score), file=FH_HTML)
            print("\t<td class=\"score_col\">%s</td>" % (gain_score), file=FH_HTML)
            print("\t<td>%s</td>\n\t</tr>" % (resolutiondate), file=FH_HTML)

        except Exception as err:
            print("Error in for " + issue.key, file=sys.stderr)
            print(str(err), file=sys.stderr)
            continue

    print("\t</tbody>", file=FH_HTML)
    print("\t</table>", file=FH_HTML)
    FH_HTML.close()

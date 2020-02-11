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
ACMG_OUT_HTML = "acmg56_body.html"
ACMG_IN_INI = "acmg56_curation.ini"


if __name__ == "__main__":

    gene_symbol_hash = {}
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')
    query_str = ('project = ISCA AND issuetype in (\"ISCA Gene Curation\") '
                 'AND labels in (\"ACMGSFv2.0\") ')
    issue_list = isca_me_util.GetIssuesByJQL(jira, query_str, sys.stdout)
    designated_fields = ['Gene Symbol',
                         'OMIM Link',
                         'ISCA Haploinsufficiency score',
                         'ISCA Triplosensitivity score',
                         'Status']
    for issue in issue_list:

        # gene_symbol
        try:
            value_dict = isca_me_util.IssueEntries(issue, ISCA_dict, designated_fields)
            gene_symbol = value_dict['Gene Symbol']
            gene_omim = value_dict['OMIM Link'].split('/')[-1]
            gain_score = value_dict['ISCA Triplosensitivity score']
            loss_score = value_dict['ISCA Haploinsufficiency score']
            status = value_dict['Status'] if value_dict['Status'] != "Closed" else ""
            if gene_symbol in gene_symbol_hash:
                raise Exception(gene_symbol + " already in gene_symbol_hash")

            gene_symbol_hash[gene_symbol] = {}
            gene_symbol_hash[gene_symbol]["omim"] = gene_omim
            gene_symbol_hash[gene_symbol]["gain_score"] = gain_score
            gene_symbol_hash[gene_symbol]["loss_score"] = loss_score
            gene_symbol_hash[gene_symbol]["status"] = status

        except Exception as err:
            print("Error in get gene_symbol or id for {} as {}".format(issue.key, str(err)),
                  file=sys.stderr)
            continue

    FH_HTML = open(ACMG_OUT_HTML, 'w')
    FH_IN = open(ACMG_IN_INI)
    for line in FH_IN:
        line_split = line.split("\t")
        phenotype = line_split[0]
        if phenotype != "":
            print("\t<tr><th colspan=\"8\">%s</th></tr>" % (phenotype), file=FH_HTML)

        acmg_gene = line_split[4].strip()
        if acmg_gene == '' or acmg_gene not in gene_symbol_hash:
            print("Error in get gene_symbol or id for " + acmg_gene, file=sys.stderr)
            continue

        mim_disorder_list = line_split[1].split(",")
        mim_disorder_html = ",".join(["<a href=\"https://omim.org/entry/" + it.strip()
                                     + "\" target=\"_blank\">" + it.strip()
                                     + "</a>" for it in mim_disorder_list])

        pmid_list = line_split[2].split(",")
        pmid_html = ",".join(["<a href=\"/pubmed/" + it.strip()
                             + "\" target=\"_blank\">" + it.strip()
                             + "</a>" for it in pmid_list])

        mim_gene_list = gene_symbol_hash[acmg_gene]['omim'].split(",")
        mim_gene_html = ",".join(["<a href=\"https://omim.org/entry/" + it.strip()
                                 + "\" target=\"_blank\">" + it.strip()
                                 + "</a>" for it in mim_gene_list])

        # loss_score_star = True if '*' in line_split[6] else False
        # gain_score_star = True if '*' in line_split[7] else False

        print("\t<tr>\n\t<td>%s</td>" % (mim_disorder_html), file=FH_HTML)
        print("\t<td>%s</td>" % (pmid_html), file=FH_HTML)
        print("\t<td>%s</td>" % (line_split[3]), file=FH_HTML)
        print("\t<td><a href=\"clingen_gene.cgi?sym=%s\" target=\"_blank\">%s</a></td>" % (
            acmg_gene, acmg_gene),
              file=FH_HTML)
        print("\t<td>%s</td>" % (mim_gene_html), file=FH_HTML)
        print("\t<td>%s</td>" % (gene_symbol_hash[acmg_gene]['loss_score']), file=FH_HTML)
        print("\t<td>%s</td>\n\t</tr>" % (gene_symbol_hash[acmg_gene]['gain_score']), file=FH_HTML)
    print("</div>", file=FH_HTML)

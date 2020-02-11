"""
 Need a process to dump Gene Issues from Jira (daily to start with)
     * Update data dictionary
     * Look to see if Gene has been withdrawn from Entrez Gene
     ** if yes, update Jira
     * write log of activity
     * get status and resolution to update home page with stats
"""
import os
import sys
import datetime
import gzip
import subprocess
import isca_me_util

# config file
DATA_DIR = '../conf'
CONFIG = os.path.join(DATA_DIR, '.isca_config')
STD_FIELD_FILE = os.path.join(DATA_DIR, 'standard_field.ini')
# your code need file as ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
GENE_INFO_FILE = 'Homo_sapiens.gene_info.gz'
OUTPUT_FILE = 'ISCA_Gene.txt'
LOG_FILE = 'log/' + datetime.date.today().strftime("%Y-%m-%d") + '_log.txt'
STAT_HTML = 'stats.html'

FILTER_ID = 10650  # filter ISCA_Public


def ReadGene(gene_file):
    symbol_hash, alias_hash = {}, {}
    FH_GENE = gzip.open(gene_file, 'rt')
    for line in FH_GENE:
        if len(line.strip()) == 0 or line.strip().startswith('#'):
            continue
        line_list = line.strip().split('\t')
        gene_id = line_list[1].strip()
        gene_symbol = line_list[2].strip()
        alias = line_list[4].strip()
        symbol_hash[gene_id] = gene_symbol
        if alias != '-':
            alias_hash[gene_id] = alias.replace('|', ',')
    FH_GENE.close()
    return (symbol_hash, alias_hash)


if __name__ == "__main__":
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')

    issue_list = isca_me_util.GetIssuesByJQL(jira, 'filter=' + str(FILTER_ID), sys.stdout)

    (symbol_hash, alias_hash) = ReadGene(GENE_INFO_FILE)

    designated_fields = [
                          'Resolution',
                          'Status',
                          'Type']

    rev_fin, prim_rev, sec_rev, group_rev, await_rev = 0, 0, 0, 0, 0
    FH_OUT_TMP = open(OUTPUT_FILE+'.tmp', 'w')
    FH_LOG = open(LOG_FILE, 'w')
    FH_REGION_COMPLETE = open("stat_region_complete.html", "w")
    FH_GENE_COMPLETE = open("stat_gene_complete.html", "w")
    FH_REGION_PRIMARY = open("stat_region_primary.html", "w")
    FH_GENE_PRIMARY = open("stat_gene_primary.html", "w")
    FH_REGION_SECOND = open("stat_region_secondary.html", "w")
    FH_GENE_SECOND = open("stat_gene_secondary.html", "w")
    FH_REGION_GROUP = open("stat_region_group.html", "w")
    FH_GENE_GROUP = open("stat_gene_group.html", "w")
    for issue in issue_list:
        try:
            value_dict = isca_me_util.IssueEntries(issue, ISCA_dict, designated_fields)

            if value_dict['Resolution'] == '':
                value_dict['Resolution'] = 'not resolved'

            print("ISSUE: %s\t%s\t%s" % (
                issue.key, value_dict['Status'], value_dict['Resolution']),
                  file=FH_LOG)

            region_name = ''
            if hasattr(issue.fields, ISCA_dict['ISCA Region Name']):
                if getattr(issue.fields, ISCA_dict['ISCA Region Name']) is not None:
                    region_name = getattr(issue.fields, ISCA_dict['ISCA Region Name']).strip()

            gene_symbol = ''
            if hasattr(issue.fields, ISCA_dict['Gene Symbol']):
                if getattr(issue.fields, ISCA_dict['Gene Symbol']) is not None:
                    gene_symbol = getattr(issue.fields, ISCA_dict['Gene Symbol'])

            gene_type = ''
            if hasattr(issue.fields, ISCA_dict['Gene Type']):
                if getattr(issue.fields, ISCA_dict['Gene Type']) is not None:
                    gene_type = getattr(issue.fields, ISCA_dict['Gene Type'])

            gene_id = ''
            if hasattr(issue.fields, ISCA_dict['Link to Gene']):
                if getattr(issue.fields, ISCA_dict['Link to Gene']) is not None:
                    gene_id = getattr(issue.fields, ISCA_dict['Link to Gene']).split('/')[-1]

            status, resolution = value_dict['Status'], value_dict['Resolution']
            if status == 'Closed' and resolution == "Won't Fix":
                pass
            elif status == 'Closed':
                rev_fin += 1
                if value_dict['Type'] == 'ISCA Gene Curation':
                    print("\t<tr>\n\t<td>%s</td>" % (gene_symbol), file=FH_GENE_COMPLETE)
                    print(("\t<td><a href=\"clingen_gene.cgi?sym=%s\" target=\"_blank\">%s"
                           "</a></td>\n\t</tr>") % (gene_symbol, issue.key),
                          file=FH_GENE_COMPLETE)
                else:
                    print("\t<tr>\n\t<td>%s</td>" % (region_name), file=FH_REGION_COMPLETE)
                    print(("\t<td><a href=\"clingen_region.cgi?id=%s\" target=\"_blank\">%s"
                           "</a></td>\n\t</tr>") % (issue.key, issue.key),
                          file=FH_REGION_COMPLETE)
            elif status == 'Under Primary Review':
                prim_rev += 1
                if value_dict['Type'] == 'ISCA Gene Curation':
                    print("\t<tr>\n\t<td>%s</td>" % (gene_symbol), file=FH_GENE_PRIMARY)
                    print(("\t<td><a href=\"clingen_gene.cgi?sym=%s\" target=\"_blank\">%s"
                           "</a></td>\n\t</tr>") % (gene_symbol, issue.key),
                          file=FH_GENE_PRIMARY)
                else:
                    print("\t<tr>\n\t<td>%s</td>" % (region_name), file=FH_REGION_PRIMARY)
                    print(("\t<td><a href=\"clingen_region.cgi?id=%s\" target=\"_blank\">%s"
                          "</a></td>\n\t</tr>") % (issue.key, issue.key),
                          file=FH_REGION_PRIMARY)
            elif status == 'Under Secondary Review':
                sec_rev += 1
                if value_dict['Type'] == 'ISCA Gene Curation':
                    print("\t<tr>\n\t<td>%s</td>" % (gene_symbol), file=FH_GENE_SECOND)
                    print(("\t<td><a href=\"clingen_gene.cgi?sym=%s\" target=\"_blank\">%s"
                          "</a></td>\n\t</tr>") % (gene_symbol, issue.key),
                          file=FH_GENE_SECOND)
                else:
                    print("\t<tr>\n\t<td>%s</td>" % (region_name), file=FH_REGION_SECOND)
                    print(("\t<td><a href=\"clingen_region.cgi?id=%s\" target=\"_blank\">%s"
                           "</a></td>\n\t</tr>") % (issue.key, issue.key),
                          file=FH_REGION_SECOND)
            elif status == 'Under Group Review':
                if value_dict['Type'] == 'ISCA Gene Curation':
                    print("\t<tr>\n\t<td>%s</td>" % (gene_symbol), file=FH_GENE_GROUP)
                    print(("\t<td><a href=\"clingen_gene.cgi?sym=%s\" target=\"_blank\">%s"
                           "</a></td>\n\t</tr>") % (gene_symbol, issue.key),
                          file=FH_GENE_GROUP)
                else:
                    print("\t<tr>\n\t<td>%s</td>" % (region_name), file=FH_REGION_GROUP)
                    print(("\t<td><a href=\"clingen_region.cgi?id=%s\" target=\"_blank\">%s"
                          "</a></td>\n\t</tr>") % (issue.key, issue.key),
                          file=FH_REGION_GROUP)
                group_rev += 1
            else:
                await_rev += 1

            if gene_id not in symbol_hash and gene_type == "withdrawn":
                print(("Newly withdrawn gene:%s: %s(%s): Update Status->Close "
                       "and Resolution->Won\'t Fix") % (issue.key, gene_id, gene_symbol),
                      file=FH_LOG)
                # Note: for right now, don't do this until you are sure you
                # can set resolution to 'Won't Fix';
            if gene_type == 'withdrawn':
                print("Gene is already withdrawn: %s (%s): %s" % (gene_id,
                                                                  gene_symbol, issue.key),
                      file=FH_LOG)
            if gene_id in alias_hash:
                ali_list = alias_hash[gene_id].split(',')
                for item in ali_list:
                    print("%s\t%s" % (item, symbol_hash[gene_id]), file=FH_OUT_TMP)
            if gene_id in symbol_hash:
                print("%s\t%s" % (symbol_hash[gene_id], symbol_hash[gene_id]), file=FH_OUT_TMP)
        except Exception as err:
            print("Error in " + issue.key + '\t' + str(err), file=FH_LOG)
            continue

    # sort gene
    FH_OUT_TMP.close()
    FH_LOG.close()
    FH_OUT_SORT = open(OUTPUT_FILE + '.sort', 'w')
    subprocess.call(['sort', '-u', OUTPUT_FILE + '.tmp'], stdout=FH_OUT_SORT)
    FH_OUT_SORT.close()
    subprocess.call(['mv', OUTPUT_FILE + '.sort', OUTPUT_FILE])

    # stat html
    FH_HTML = open(STAT_HTML, 'w')
    print("<h3>Gene/Region Curation Stats</h3>", file=FH_HTML)
    print("<table data-jig=\"ncbigrid\">", file=FH_HTML)
    print(("\t<tr>\n\t<td>Review Complete</td>\n\t<td>"
           "<a href=\"stat_details.shtml#complete_tabs\" >%s"
           "</a></td></tr>") % ('{:,d}'.format(rev_fin)),
          file=FH_HTML)
    print(("\t<tr>\n\t<td>Under Primary Review</td>\n\t<td>"
           "<a href=\"stat_details.shtml#primary_tabs\" >%s"
           "</a></td></tr>") % ('{:,d}'.format(prim_rev)),
          file=FH_HTML)
    print(("\t<tr>\n\t<td>Under Secondary Review</td>\n\t<td>"
           "<a href=\"stat_details.shtml#secondary_tabs\" >%s"
           "</a></td></tr>") % ('{:,d}'.format(sec_rev)),
          file=FH_HTML)
    print(("\t<tr>\n\t<td>Under Group Review</td>\n\t<td>"
           "<a href=\"stat_details.shtml#group_tabs\" >%s"
           "</a></td></tr>") % ('{:,d}'.format(group_rev)),
          file=FH_HTML)
    print("\t<tr>\n\t<td>Awaiting Review</td>\n\t<td>%s</td></tr>" % ('{:,d}'.format(await_rev)),
          file=FH_HTML)
    print("</table>", file=FH_HTML)
    FH_HTML.close()

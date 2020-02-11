""" create region.idx used for cgi
    the rows in file are sorted based on loc, namely (chr, start, stop)
"""
import sys
import os
import isca_me_util

# config file
DATA_DIR = '../conf'
CONFIG = os.path.join(DATA_DIR, '.isca_config')
STD_FIELD_FILE = os.path.join(DATA_DIR, 'standard_field.ini')
# filter id
FILTER_ID = 10632

if __name__ == "__main__":
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')
    issue_list = isca_me_util.GetIssuesByJQL(jira, 'filter=' + str(FILTER_ID), sys.stdout)

    ret_list = []
    gene_loc_dict, region_loc_dict = {}, {}
    region_name_dict = {}
    designated_fields = ['Resolution',
                         'Status',
                         'GRCh37 Genome Position',
                         'Type',
                         'Summary',
                         'ISCA Haploinsufficiency score',
                         'ISCA Triplosensitivity score',
                         'OMIM Link',
                         'ExAC pLI score']
    for issue in issue_list:
        try:
            value_dict = isca_me_util.IssueEntries(issue, ISCA_dict, designated_fields)

            # gene tickect does not have region name
            region_name = ''
            if hasattr(issue.fields, ISCA_dict['ISCA Region Name']):
                if getattr(issue.fields, ISCA_dict['ISCA Region Name']) is not None:
                    region_name = getattr(issue.fields, ISCA_dict['ISCA Region Name']).strip()

            # ingore gene_type withdrawn
            gene_type = ''
            if hasattr(issue.fields, ISCA_dict['Gene Type']):
                if getattr(issue.fields, ISCA_dict['Gene Type']) is not None:
                    gene_type = getattr(issue.fields, ISCA_dict['Gene Type'])
            if gene_type == 'withdrawn':
                continue

            # resolution and status, ignore close and won't fix ticket
            resolution, status = value_dict['Resolution'], value_dict['Status']
            cur_status = ''
            if status == 'Closed' and resolution == "Won't Fix":
                continue
            elif status == 'Closed' and resolution == 'Complete':
                cur_status = 'Complete'
            elif status == 'Open':
                cur_status = 'Awaiting Review'
            else:
                cur_status = status

            if status == 'Closed' and resolution == "Duplicate":
                continue

            # prepare chr_num, start, stop used just for sorting
            (chr, start, stop) = isca_me_util.ProcessGenomePosition(
                value_dict['GRCh37 Genome Position'])
            chr_num = -1
            if chr.isdigit():
                chr_num = int(chr)
            elif chr == 'X':
                chr_num = 23
            elif chr == 'Y':
                chr_num = 24
            else:  # other case to the last
                chr_num = 25

            # store gene/region location used for overlap calculation
            if value_dict['Type'] == 'ISCA Gene Curation':
                if start != '' and stop != '':
                    if chr not in gene_loc_dict:
                        gene_loc_dict[chr] = []
                    gene_loc_dict[chr].append([start, stop, issue.key])
            else:
                if start != '' and stop != '':
                    if chr not in region_loc_dict:
                        region_loc_dict[chr] = []
                    region_loc_dict[chr].append([start, stop, issue.key])
                    region_name_dict[issue.key] = (region_name if region_name != ''
                                                   else value_dict['Summary'])

            gain_score = (value_dict['ISCA Triplosensitivity score']
                          if cur_status == 'Complete' else 'N/A')
            loss_score = (value_dict['ISCA Haploinsufficiency score']
                          if cur_status == 'Complete' else 'N/A')

            omim = ''
            if hasattr(issue.fields, ISCA_dict['OMIM Link']):
                if getattr(issue.fields, ISCA_dict['OMIM Link']) is not None:
                    omim = getattr(issue.fields, ISCA_dict['OMIM Link']).strip()
                    omim = omim.split('/')[-1].split('?')[0]
            pli = ''
            if hasattr(issue.fields, ISCA_dict['ExAC pLI score']):
                if getattr(issue.fields, ISCA_dict['ExAC pLI score']) is not None:
                    pli = getattr(issue.fields, ISCA_dict['ExAC pLI score'])
            record = {
                          'loc': value_dict['GRCh37 Genome Position'],
                          'key': issue.key,
                          'type': value_dict['Type'],
                          'cur_status': cur_status,
                          'reg_name': region_name,
                          'chr_num': chr_num,
                          'start': start,
                          'stop': stop,
                          'gain_score': gain_score,
                          'loss_score': loss_score,
                          'pli': pli,
                          'omim': omim
                     }
            ret_list.append(record)
        except Exception as err:
            print("Error in " + issue.key + "with error: " + str(err), file=sys.stderr)

    # sort the list based on chr, start, stop
    sorted_ret_list = sorted(ret_list,
                             key=lambda x: (x['chr_num'],
                                            -1 if x['start'] == '' else int(x['start']),
                                            -1 if x['stop'] == '' else int(x['stop'])))

    FH_OUT = open('region.idx', 'w')
    for item in sorted_ret_list:
        print("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            item['loc'], item['key'], item['type'], item['cur_status'],
            item['reg_name'], item['gain_score'],
            item['loss_score'], item['pli'], item['omim']),
              file=FH_OUT)
    FH_OUT.close()

    # overlap info
    FH_OVER = open('gene_overlap.idx', 'w')
    for chr_id in gene_loc_dict.keys():
        if chr_id not in region_loc_dict:
            continue
        gene_list = gene_loc_dict[chr_id]
        region_list = region_loc_dict[chr_id]
        for gene_item in gene_list:
            gene_start = gene_item[0]
            gene_stop = gene_item[1]
            for region_item in region_list:
                region_start = region_item[0]
                region_stop = region_item[1]
                if region_start <= gene_stop and region_stop >= gene_start:
                    print("%s\t%s\t%s" % (gene_item[2], region_item[2],
                                          region_name_dict[region_item[2]]),
                          file=FH_OVER)
    FH_OVER.close()

""" Generate ftp files
       ClinGen_region_curation_list.tsv
       ClinGen_gene_curation_list.tsv
       ClinGen_haploinsufficiency_gene.bed
       ClinGen_triplosensitivity_gene.bed
     Put log files to log/date_log.txt
"""

import os
import sys
import datetime
import subprocess
import isca_me_util

# config file
DATA_DIR = '../conf'
CONFIG = os.path.join(DATA_DIR, '.isca_config')
STD_FIELD_FILE = os.path.join(DATA_DIR, 'standard_field.ini')
LOG_FILE = './log/' + datetime.date.today().strftime("%Y-%m-%d") + '_log.txt'

# output files
GENE_FILE_GRCh37 = 'ClinGen_gene_curation_list_GRCh37.tsv'
GENE_FILE_GRCh38 = 'ClinGen_gene_curation_list_GRCh38.tsv'
REGION_FILE_GRCh37 = 'ClinGen_region_curation_list_GRCh37.tsv'
REGION_FILE_GRCh38 = 'ClinGen_region_curation_list_GRCh38.tsv'
HAP_FILE_GRCh37 = 'ClinGen_haploinsufficiency_gene_GRCh37.bed'
HAP_FILE_GRCh38 = 'ClinGen_haploinsufficiency_gene_GRCh38.bed'
TRIP_FILE_GRCh37 = 'ClinGen_triplosensitivity_gene_GRCh37.bed'
TRIP_FILE_GRCh38 = 'ClinGen_triplosensitivity_gene_GRCh38.bed'

# filter id
GENE_FILTER_ID = 10771
REGION_FILTER_ID = 10772


def PostProcessLoss(value_dict):
    isca_loss_score = value_dict['ISCA Haploinsufficiency score']
    val = value_dict['ISCA Haploinsufficiency score']
    loss_text = ''

    if val == '3':
        loss_text = 'Sufficient evidence for dosage pathogenicity'
    elif val == '2':
        loss_text = 'Some evidence for dosage pathogenicity'
    elif val == '1':
        loss_text = 'Little evidence for dosage pathogenicity'
    elif val == '0':
        loss_text = 'No evidence available'
    elif val == '-1':
        loss_text = 'Gene not in scope'
    elif val.strip().startswith('30:') or val.strip().startswith('40:'):
        tmp_list = val.strip().split(':')
        isca_loss_score = tmp_list[0].strip()
        loss_text = tmp_list[1].strip()
    else:
        loss_text = val
    return (isca_loss_score, loss_text)


def PostProcessGain(value_dict):
    isca_gain_score = val = value_dict['ISCA Triplosensitivity score']

    if val == '3':
        gain_text = 'Sufficient evidence for dosage pathogenicity'
    elif val == '2':
        gain_text = 'Some evidence for dosage pathogenicity'
    elif val == '1':
        gain_text = 'Little evidence for dosage pathogenicity'
    elif val == '0':
        gain_text = 'No evidence available'
    elif val == '-1':
        gain_text = 'Gene not in scope'
    elif val.strip().startswith('30:') or val.strip().startswith('40:'):
        tmp_list = val.strip().split(':')
        isca_gain_score = tmp_list[0].strip()
        gain_text = tmp_list[1].strip()
    else:
        gain_text = val
    return (isca_gain_score, gain_text)


def process_gene_loc(gene_loc):
    tmp_list = gene_loc.split(':')
    chr = tmp_list[0].strip()
    start = stop = ''
    if len(tmp_list) > 1:
        pos_str = tmp_list[1].strip()
        pos_list = pos_str.split('-')
        start = int(pos_list[0].strip()) - 1
        if len(pos_list) > 1:
            stop = pos_list[1].strip()
    return (chr, start, stop)


def OutputLine(file_type, value_dict, issue_key):

    # gain, loss score
    (isca_loss_score, loss_text) = PostProcessLoss(value_dict)
    (isca_gain_score, gain_text) = PostProcessGain(value_dict)

    # pmid
    loss_pmid_1 = isca_me_util.CleanPMID(value_dict['Loss PMID 1'],
                                         FH_LOG, issue_key, value_dict['Assignee'])
    loss_pmid_2 = isca_me_util.CleanPMID(value_dict['Loss PMID 2'],
                                         FH_LOG, issue_key, value_dict['Assignee'])
    loss_pmid_3 = isca_me_util.CleanPMID(value_dict['Loss PMID 3'],
                                         FH_LOG, issue_key, value_dict['Assignee'])
    gain_pmid_1 = isca_me_util.CleanPMID(value_dict['Gain PMID 1'],
                                         FH_LOG, issue_key, value_dict['Assignee'])
    gain_pmid_2 = isca_me_util.CleanPMID(value_dict['Gain PMID 2'],
                                         FH_LOG, issue_key, value_dict['Assignee'])
    gain_pmid_3 = isca_me_util.CleanPMID(value_dict['Gain PMID 3'],
                                         FH_LOG, issue_key, value_dict['Assignee'])

    # gain_loss omim
    loss_omim_list = isca_me_util.CleanOMIM(value_dict['Loss phenotype OMIM ID'],
                                            FH_LOG, issue_key, value_dict['Assignee'])
    gain_omim_list = isca_me_util.CleanOMIM(value_dict['Triplosensitive phenotype OMIM ID'],
                                            FH_LOG, issue_key, value_dict['Assignee'])
    # loc
    value_dict['GRCh37 Genome Position'] = value_dict['GRCh37 Genome Position'].replace(',', '')
    gene_GRCh37_loc = value_dict['GRCh37 Genome Position']
    if not value_dict['GRCh37 Genome Position'].startswith('chr'):
        gene_GRCh37_loc = 'tbd'
        print("BAD LOC\t%s\t%s\t%s" % (issue_key, value_dict['GRCh37 Genome Position'],
                                       value_dict['Assignee']), file=FH_LOG)

    (chr_GRCh37, start_GRCh37, stop_GRCh37) = process_gene_loc(gene_GRCh37_loc)
    loc_hash = {}
    loc_hash['GRCh37'] = {}
    loc_hash['GRCh37']['FH_GENE_TMP'] = FH_GENE_GRCh37_TMP
    loc_hash['GRCh37']['FH_HAP_TMP'] = FH_HAP_GRCh37_TMP
    loc_hash['GRCh37']['FH_TRIP_TMP'] = FH_TRIP_GRCh37_TMP
    loc_hash['GRCh37']['FH_REGION_TMP'] = FH_REGION_GRCh37_TMP
    loc_hash['GRCh37']['loc'] = gene_GRCh37_loc
    loc_hash['GRCh37']['chr'] = chr_GRCh37
    loc_hash['GRCh37']['start'] = start_GRCh37
    loc_hash['GRCh37']['stop'] = stop_GRCh37

    value_dict['GRCh38 Genome Position'] = value_dict['GRCh38 Genome Position'].replace(',', '')
    gene_GRCh38_loc = value_dict['GRCh38 Genome Position']
    if not value_dict['GRCh38 Genome Position'].startswith('chr'):
        gene_GRCh38_loc = 'tbd'
        print("BAD LOC\t%s\t%s\t%s" % (issue_key, value_dict['GRCh38 Genome Position'],
                                       value_dict['Assignee']), file=FH_LOG)

    (chr_GRCh38, start_GRCh38, stop_GRCh38) = process_gene_loc(gene_GRCh38_loc)
    loc_hash['GRCh38'] = {}
    loc_hash['GRCh38']['FH_GENE_TMP'] = FH_GENE_GRCh38_TMP
    loc_hash['GRCh38']['FH_HAP_TMP'] = FH_HAP_GRCh38_TMP
    loc_hash['GRCh38']['FH_TRIP_TMP'] = FH_TRIP_GRCh38_TMP
    loc_hash['GRCh38']['FH_REGION_TMP'] = FH_REGION_GRCh38_TMP
    loc_hash['GRCh38']['loc'] = gene_GRCh38_loc
    loc_hash['GRCh38']['chr'] = chr_GRCh38
    loc_hash['GRCh38']['start'] = start_GRCh38
    loc_hash['GRCh38']['stop'] = stop_GRCh38

    if file_type == 'GENE':
        # populate gene and two bed files
        if value_dict['Gene Symbol'] == 'na':
            print("ERROR! Data with no gene symbol\t%s" % (issue_key), file=FH_LOG)
        for assembly in loc_hash.keys():
            # write to gene file
            print(("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
                   "\t%s\t%s\t%s\t%s\t%s\t%s\t%s") % (
                value_dict['Gene Symbol'],
                value_dict['Link to Gene'].strip().split('/')[-1].strip(),
                value_dict['CytoBand'], loc_hash[assembly]['loc'],
                isca_loss_score, loss_text, loss_pmid_1, loss_pmid_2, loss_pmid_3,
                isca_gain_score, gain_text, gain_pmid_1, gain_pmid_2, gain_pmid_3,
                value_dict['Resolved'].split('T')[0].strip(),
                ",".join(loss_omim_list), ",".join(gain_omim_list)),
                  file=loc_hash[assembly]['FH_GENE_TMP'])

            # if isca_loss_score == 'Dosage sensitivity unlikely':
            #     isca_loss_score = 99
            # if isca_gain_score == 'Dosage sensitivity unlikely':
            #     isca_gain_score = 99
            # if isca_loss_score == 'Gene associated with autosomal recessive phenotype':
            #     isca_loss_score = 50
            # if isca_gain_score == 'Gene associated with autosomal recessive phenotype':
            #     isca_gain_score = 50

            print("%s\t%s\t%s\t%s\t%s" % (loc_hash[assembly]['chr'],
                                          loc_hash[assembly]['start'],
                                          loc_hash[assembly]['stop'],
                                          value_dict['Gene Symbol'],
                                          isca_loss_score), file=loc_hash[assembly]['FH_HAP_TMP'])
            print("%s\t%s\t%s\t%s\t%s" % (loc_hash[assembly]['chr'],
                                          loc_hash[assembly]['start'],
                                          loc_hash[assembly]['stop'],
                                          value_dict['Gene Symbol'],
                                          isca_gain_score), file=loc_hash[assembly]['FH_TRIP_TMP'])

    elif file_type == 'REGION':
        for assembly in loc_hash.keys():
            # populate region file
            print("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                issue_key, value_dict['ISCA Region Name'], value_dict['CytoBand'],
                loc_hash[assembly]['loc'],
                isca_loss_score, loss_text, loss_pmid_1, loss_pmid_2, loss_pmid_3,
                isca_gain_score, gain_text, gain_pmid_1, gain_pmid_2, gain_pmid_3,
                value_dict['Resolved'].split('T')[0].strip(),
                ",".join(loss_omim_list), ",".join(gain_omim_list)),
                file=loc_hash[assembly]['FH_REGION_TMP'])
    else:
        print("Error: wrong file_type, should be either GENE or REGION, STOP", file=sys.stderr)
        sys.exit(1)


def GenerateSummaryFile(jira, filter_id, standard_field_dict, file_type, designated_field_keys):
    issue_list = isca_me_util.GetIssuesByJQL(jira, 'filter=' + str(filter_id), sys.stdout)
    for issue in issue_list:
        value_dict = isca_me_util.IssueEntries(issue, standard_field_dict, designated_field_keys)

        # gene tickect does not have region name
        region_name = ''
        if hasattr(issue.fields, ISCA_dict['ISCA Region Name']):
            if getattr(issue.fields, ISCA_dict['ISCA Region Name']) is not None:
                region_name = getattr(issue.fields, ISCA_dict['ISCA Region Name']).strip()
        value_dict['ISCA Region Name'] = region_name

        OutputLine(file_type, value_dict, issue.key)


if __name__ == "__main__":
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')

    FH_LOG = open(LOG_FILE, 'w')

    query_fields = ['Loss PMID 1',
                    'Loss PMID 2',
                    'Loss PMID 3',
                    'Gain PMID 1',
                    'Gain PMID 2',
                    'Gain PMID 3',
                    'Assignee',
                    'ISCA Haploinsufficiency score',
                    'ISCA Triplosensitivity score',
                    'GRCh37 Genome Position',
                    'GRCh38 Genome Position',
                    'Gene Symbol',
                    'Link to Gene',
                    'CytoBand',
                    'Resolved',
                    'Loss phenotype OMIM ID',
                    'Triplosensitive phenotype OMIM ID']

    # GENE and Bed tmp files
    FH_GENE_GRCh37_TMP = open(GENE_FILE_GRCh37+'.tmp', 'w')
    FH_GENE_GRCh38_TMP = open(GENE_FILE_GRCh38+'.tmp', 'w')
    FH_HAP_GRCh37_TMP = open(HAP_FILE_GRCh37+'.tmp', 'w')
    FH_HAP_GRCh38_TMP = open(HAP_FILE_GRCh38+'.tmp', 'w')
    FH_TRIP_GRCh37_TMP = open(TRIP_FILE_GRCh37+'.tmp', 'w')
    FH_TRIP_GRCh38_TMP = open(TRIP_FILE_GRCh38+'.tmp', 'w')
    FH_REGION_GRCh37_TMP = open(REGION_FILE_GRCh37+'.tmp', 'w')
    FH_REGION_GRCh38_TMP = open(REGION_FILE_GRCh38+'.tmp', 'w')

    GenerateSummaryFile(jira, GENE_FILTER_ID, ISCA_dict, 'GENE', query_fields)

    FH_GENE_GRCh37_TMP.close()
    FH_GENE_GRCh38_TMP.close()
    FH_HAP_GRCh37_TMP.close()
    FH_HAP_GRCh38_TMP.close()
    FH_TRIP_GRCh37_TMP.close()
    FH_TRIP_GRCh38_TMP.close()

    # Region tmp files
    GenerateSummaryFile(jira, REGION_FILTER_ID, ISCA_dict, 'REGION', query_fields)
    FH_REGION_GRCh37_TMP.close()
    FH_REGION_GRCh38_TMP.close()

    # generate gene region file
    FH_GENE_GRCh37 = open(GENE_FILE_GRCh37, 'w')
    FH_REGION_GRCh37 = open(REGION_FILE_GRCh37, 'w')
    FH_GENE_GRCh38 = open(GENE_FILE_GRCh38, 'w')
    FH_REGION_GRCh38 = open(REGION_FILE_GRCh38, 'w')
    FH_HAP_GRCh37 = open(HAP_FILE_GRCh37, 'w')
    FH_HAP_GRCh38 = open(HAP_FILE_GRCh38, 'w')
    FH_TRIP_GRCh37 = open(TRIP_FILE_GRCh37, 'w')
    FH_TRIP_GRCh38 = open(TRIP_FILE_GRCh38, 'w')
    out_hash = {}
    out_hash['GRCh37'] = {}
    out_hash['GRCh37']['FH_GENE'] = FH_GENE_GRCh37
    out_hash['GRCh37']['FH_REGION'] = FH_REGION_GRCh37
    out_hash['GRCh37']['FH_HAP'] = FH_HAP_GRCh37
    out_hash['GRCh37']['FH_TRIP'] = FH_TRIP_GRCh37
    out_hash['GRCh37']['GENE_FILE'] = GENE_FILE_GRCh37
    out_hash['GRCh37']['REGION_FILE'] = REGION_FILE_GRCh37
    out_hash['GRCh37']['HAP_FILE'] = HAP_FILE_GRCh37
    out_hash['GRCh37']['TRIP_FILE'] = TRIP_FILE_GRCh37
    out_hash['GRCh37']['HG'] = 'hg19'
    out_hash['GRCh37']['Accession'] = 'GCF_000001405.13'

    out_hash['GRCh38'] = {}
    out_hash['GRCh38']['FH_GENE'] = FH_GENE_GRCh38
    out_hash['GRCh38']['FH_REGION'] = FH_REGION_GRCh38
    out_hash['GRCh38']['FH_HAP'] = FH_HAP_GRCh38
    out_hash['GRCh38']['FH_TRIP'] = FH_TRIP_GRCh38
    out_hash['GRCh38']['GENE_FILE'] = GENE_FILE_GRCh38
    out_hash['GRCh38']['REGION_FILE'] = REGION_FILE_GRCh38
    out_hash['GRCh38']['HAP_FILE'] = HAP_FILE_GRCh38
    out_hash['GRCh38']['TRIP_FILE'] = TRIP_FILE_GRCh38
    out_hash['GRCh38']['HG'] = 'hg38'
    out_hash['GRCh38']['Accession'] = 'GCF_000001405.36'

    for assembly in out_hash.keys():
        # GENE
        print("#ClinGen Gene Curation Results", file=out_hash[assembly]['FH_GENE'])
        print("#" + datetime.date.today().strftime("%d %b,%Y"),
              file=out_hash[assembly]['FH_GENE'])
        print("#Genomic Locations are reported on {} ({}): {}".format(
            assembly, out_hash[assembly]['HG'],
            out_hash[assembly]['Accession']),
              file=out_hash[assembly]['FH_GENE'])
        print("#https://www.ncbi.nlm.nih.gov/projects/dbvar/clingen",
              file=out_hash[assembly]['FH_GENE'])
        print(("#to create link: https://www.ncbi.nlm.nih.gov/projects/"
               "dbvar/clingen/clingen_gene.cgi?sym=Gene Symbol"),
              file=out_hash[assembly]['FH_GENE'])
        print(("#Gene Symbol\tGene ID\tcytoBand\tGenomic Location\tHaploinsufficiency Score"
               "\tHaploinsufficiency Description\tHaploinsufficiency PMID1"
               "\tHaploinsufficiency PMID2\tHaploinsufficiency PMID3"
               "\tTriplosensitivity Score\tTriplosensitivity Description"
               "\tTriplosensitivity PMID1\tTriplosensitivity PMID2"
               "\tTriplosensitivity PMID3\tDate Last Evaluated"
               "\tLoss phenotype OMIM ID\tTriplosensitive phenotype OMIM ID"),
              file=out_hash[assembly]['FH_GENE'])
        out_hash[assembly]['FH_GENE'].flush()
        subprocess.call(['sort', '-k 1', out_hash[assembly]['GENE_FILE'] + '.tmp'],
                        stdout=out_hash[assembly]['FH_GENE'])
        out_hash[assembly]['FH_GENE'].close()

        # REGION
        print("#ClinGen Region Curation Results", file=out_hash[assembly]['FH_REGION'])
        print("#" + datetime.date.today().strftime("%d %b,%Y"),
              file=out_hash[assembly]['FH_REGION'])
        print("#Genomic Locations are reported on {} ({}): {}".format(
            assembly, out_hash[assembly]['HG'],
            out_hash[assembly]['Accession']),
              file=out_hash[assembly]['FH_REGION'])
        print("#https://www.ncbi.nlm.nih.gov/projects/dbvar/clingen",
              file=out_hash[assembly]['FH_REGION'])
        print(("#to create link: https://www.ncbi.nlm.nih.gov/projects"
               "/dbvar/clingen/clingen_region.cgi?id=key"), file=out_hash[assembly]['FH_REGION'])
        print(("#ISCA ID\tISCA Region Name\tcytoBand\tGenomic Location"
               "\tHaploinsufficiency Score\tHaploinsufficiency Description"
               "\tHaploinsufficiency PMID1\tHaploinsufficiency PMID2\tHaploinsufficiency PMID3"
               "\tTriplosensitivity Score\tTriplosensitivity Description"
               "\tTriplosensitivity PMID1\tTriplosensitivity PMID2\tTriplosensitivity PMID3"
               "\tDate Last Evaluated\tLoss phenotype OMIM ID"
               "\tTriplosensitive phenotype OMIM ID"), file=out_hash[assembly]['FH_REGION'])
        out_hash[assembly]['FH_REGION'].flush()
        subprocess.call(['cat', out_hash[assembly]['REGION_FILE'] + '.tmp'],
                        stdout=out_hash[assembly]['FH_REGION'])
        out_hash[assembly]['FH_REGION'].close()

        # sort BED FILES
        print(("track name='ClinGen Gene Curation Haplosensitivity "
               "Scores' db={}").format(out_hash[assembly]['HG']), file=out_hash[assembly]['FH_HAP'])
        out_hash[assembly]['FH_HAP'].flush()
        subprocess.check_call(['sort', '-k 1,1', '-k 2,2', out_hash[assembly]['HAP_FILE'] + '.tmp'],
                              stdout=out_hash[assembly]['FH_HAP'])
        out_hash[assembly]['FH_HAP'].close()

        print(("track name='ClinGen Gene Curation Triplosensitivity "
               "Scores' db={}").format(out_hash[assembly]['HG']), file=out_hash[assembly]['FH_TRIP'])
        out_hash[assembly]['FH_TRIP'].flush()
        subprocess.call(['sort', '-k 1,1', '-k 2,2', out_hash[assembly]['TRIP_FILE'] + '.tmp'],
                        stdout=out_hash[assembly]['FH_TRIP'])
        out_hash[assembly]['FH_TRIP'].close()

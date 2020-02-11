""" list of functions related to external JIRA queyr,
    can be used for ISCA and Medical Exome code """

import configparser
import os
import re
import sys
import time
from jira.client import JIRA
from jinja2 import Template


def ParseLoginConfig(config_file):
    """ read standard login config file to get user and passwd"""
    user, passwd = '', ''
    config_fh = open(config_file, 'r')
    for line in config_fh:
        line_list = line.strip().split('=')
        if line_list[0].strip() == 'user':
            user = line_list[1].strip()
        elif line_list[0].strip() == 'pswd':
            passwd = line_list[1].strip()
    config_fh.close()

    return (user, passwd)


def JiraConnect(user, passwd):
    """ connect to ncbi exteral jira server """
    try:
        jira = JIRA(options={'server': 'https://dci.clinicalgenome.org/'},
                    basic_auth=(user, passwd))
        return jira
    except Exception as err:
        print("Error in connect to ncbi jira: {} \nExit".format(str(err)),
              file=sys.stderr)
        sys.exit(1)


def GetFieldDict(field_config_file, section):
    """
       Read config file field_config_file, extract key:value pair in
       "section" and return as a dict
       field_config_file format
           [ISCA]
              Gene Symbol = customfield_10030
       return field_dict as ['Gene Symbol':'customfield_10030']
    """
    field_dict = {}
    config = configparser.ConfigParser()
    config.optionxform = str
    try:
        config.read(field_config_file)
        options = config.options(section)
        for option in options:
            field_dict[option] = config.get(section, option)
    except Exception as err:
        print("ERROR from ini file({}): {}".format(field_config_file, str(err)),
              file=sys.stderr)
        sys.exit(1)

    return field_dict


def GetIssuesByJQL(jira, JQL_statement, FH_LOG=sys.stderr):
    """ return the issue list related to search of JQL_statement """
    try:
        MAX_RESULT = 500
        issue_list = []
        start_at = 0
        t0 = time.time()
        while True:
            current_result = jira.search_issues(JQL_statement,
                                                startAt=start_at,
                                                maxResults=MAX_RESULT)
            issue_list += current_result
            print(("Begin to get result, start_at %d ticket "
                   "with execution_time %.3f") % (start_at, round(time.time() - t0, 3)),
                  file=FH_LOG)
            if len(current_result) < MAX_RESULT:
                break
            else:
                start_at += MAX_RESULT
        print(("final result, start_at %d ticket "
               "with execution_time %.3f") % (start_at, round(time.time() - t0, 3)),
              file=FH_LOG)
        print("there are already %d tickets returned" % (len(issue_list)),
              file=FH_LOG)
    except Exception as inst:
        print(type(inst), file=FH_LOG)
        print(inst, file=FH_LOG)
        sys.exit(1)

    return issue_list


def IssueEntries(issue, field_dict, designated_field_keys=None):
    """ In each issue, based on field_dict,
        store field_name:value key pair into value_dict"""
    value_dict = {}
    process_list = []
    if designated_field_keys is None:
        process_list = field_dict.keys()
    else:
        process_list = designated_field_keys

    for key in process_list:
        try:
            if hasattr(issue.fields, field_dict[key]):
                value_dict[key] = ''
                if key in ['Type', 'Assignee', 'Status', 'Resolution']:
                    if getattr(issue.fields, field_dict[key]) is not None:
                        value_dict[key] = getattr(issue.fields,
                                                  field_dict[key]).name.strip()
                elif key in ['ISCA Haploinsufficiency score',
                             'ISCA Triplosensitivity score',
                             'Should be targeted?', 'Gene Type',
                             'Targeting decision based on',
                             'in medical exome v1',
                             'Loss phenotype ontology name',
                             'Triplosensitive phenotype ontology name',
                             'CGD Inheritance']:
                    if getattr(issue.fields, field_dict[key]) is not None:
                        value_dict[key] = getattr(issue.fields,
                                                  field_dict[key]).value
                elif key in ['Components']:
                    if getattr(issue.fields, field_dict[key]) is not None:
                        value_dict[key] = ','. join([item.name for item in
                                                     getattr(issue.fields, field_dict[key])])
                elif key in ['ExAC pLI score']:
                    if getattr(issue.fields, field_dict[key]) is not None:
                        value_dict[key] = getattr(issue.fields, field_dict[key])
                else:
                    if getattr(issue.fields, field_dict[key]) is not None:
                        value_dict[key] = getattr(issue.fields,
                                                  field_dict[key]).strip()
        except Exception as err:
            print("Error: {}\t{}\t{}".format(issue.key, key, str(err)),
                  file=sys.stderr)
            sys.exit(1)

    return value_dict


def ProcessGenomePosition(sub_loc):
    """ loosely parse chr:start-stop. For loc in NT,
        it could be just chr,where start, stop is None """

    loc_str = ''.join(sub_loc.upper().split())

    if not loc_str.startswith('CHR'):
        print("invalid genomic location: {}".format(sub_loc),
              file=sys.stderr)

    chr, start, stop = '', '', ''
    if loc_str.find(':') == -1:
        chr = loc_str[3:]
    else:
        loc_str_list = loc_str.split(':')
        chr = loc_str_list[0][3:]
        pos_list = loc_str_list[1].split('-')
        start = int(pos_list[0].replace(',', ''))
        stop = int(pos_list[1].replace(',', ''))
    return (chr, start, stop)


def CleanPMID(pmid_str, error_log=None, issue_key=None, issue_assignee=None):
    """ Perform mimimum clean on user-provided pubmed_id """
    if pmid_str.strip() == '':
        return ''

    test_str = ''.join(pmid_str.upper().split())
    if test_str.startswith('PMID'):
        return pmid_str.strip().replace('PMID', '').replace(':', '').strip()
    elif test_str[0].isdigit():
        return pmid_str.strip()
    else:
        if error_log is not None:
            print("BAD PMID\t{}\t{}\t{}".format(pmid_str, issue_key,
                                                issue_assignee),
                  file=error_log)
        return ''


def CleanOMIM(omim_input, error_log=sys.stdout, issue_key=None, issue_assignee=None):
    "Perform mimimum clean on user-provided omim id"
    omim_list = []
    if omim_input.strip() == '':
        return omim_list

    test_str = ''.join(omim_input.upper().split())
    input_list = test_str.split(",")
    for single in input_list:
        if single.startswith('OMIM'):
            pattern = re.compile(r"^OMIM(:)?(\d+)$")
            match_obj = pattern.match(single)
            if match_obj:
                omim_list.append(match_obj.group(2))
            else:
                print("BAD OMIMID\t%s\t%s\t%s" % (single, issue_key, issue_assignee),
                      file=error_log)
        elif single.startswith('HTTP'):
            pattern = re.compile(r"^HTTP(S)?://(WWW.)?OMIM.ORG/(ENTRY/)?(\d+)$")
            match_obj = pattern.match(single)
            if match_obj:
                omim_list.append(match_obj.group(4))
            else:
                print("BAD OMIMID\t%s\t%s\t%s" % (single, issue_key, issue_assignee),
                      file=error_log)
        else:
            pattern = re.compile(r"^(\d+)$")
            match_obj = pattern.match(single)
            if match_obj:
                omim_list.append(match_obj.group(1))
            else:
                print("BAD OMIMID\t%s\t%s\t%s" % (single, issue_key, issue_assignee),
                      file=error_log)
    return omim_list


def read_file_template(template_path, template_file):
    file_path = os.path.join(template_path, template_file)
    with open(file_path) as file_:
        file_template = Template(file_.read(), trim_blocks=True, lstrip_blocks=True)
    return file_template


def CleanOntology(ontology_type, ontology_id, error_log=sys.stdout):
    '''Perform minimum clean on user-provided ontology type and id
       the valid value should have valid display_id '''

    # cmp_ontology_type = ontology_type.strip().lower()
    cmp_ontology_type = ontology_type.strip().lower()
    display_type, display_id, display_base_url, display_id_prefix = '', '', '', ''

    # display_type and base_url (except monarch)
    if cmp_ontology_type == 'monarch':
        display_type = 'Monarch'
    elif cmp_ontology_type == 'orphanet':
        display_type = 'OrphaNet'
        display_base_url = 'http://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=EN&Expert='
    elif cmp_ontology_type == 'disease ontology':
        display_type = 'Disease Ontology'
        display_base_url = 'http://disease-ontology.org/term/DOID:'
    elif cmp_ontology_type == 'medgen':
        display_type = 'MedGen'
        display_base_url = 'https://www.ncbi.nlm.nih.gov/medgen/'

    # display_id
    if cmp_ontology_type in ['orphanet', 'disease ontology', 'medgen']:
        pattern = re.compile(r"^(\d+)$")
        match_obj = pattern.match(ontology_id.strip())
        if match_obj:
            display_id = ontology_id
        else:
            print("BAD Oncology id/name\t%s" % (ontology_id), file=error_log)
    elif cmp_ontology_type == 'monarch':
        test_str = ''.join(ontology_id.upper().split())
        pattern = re.compile(r"^(MP|MONDO)?(:)?(\d+)$")
        match_obj = pattern.match(test_str)
        if match_obj:
            monarch_prefix = match_obj.group(1)
            monarch_id = match_obj.group(3)
            if monarch_prefix is None:
                print("BAD Oncology Monarch without MONDO or MP \t%s" % (ontology_id),
                      file=error_log)
            elif monarch_prefix == 'MP':
                display_id = monarch_id
                display_id_prefix = 'MP:'
                display_base_url = 'https://monarchinitiative.org/phenotype/MP:'
            elif monarch_prefix == 'MONDO':
                display_id = monarch_id
                display_id_prefix = 'MONDO:'
                display_base_url = 'https://monarchinitiative.org/disease/MONDO:'
        else:
            print("BAD Oncology Monarch id/name\t%s" % (ontology_id),
                  file=error_log)
    return (display_type, display_id, display_id_prefix, display_base_url)


def read_mim_file(mim_file):
    # READ static FILE
    mim_dict = {}
    FH_MIM = open(mim_file, 'r', encoding="ISO-8859-1")
    for line in FH_MIM:
        line_list = line.strip().split('\t')
        mim_dict[line_list[0].strip()] = line_list[1].strip()
    FH_MIM.close()

    return mim_dict


def read_gene_idx_file(gene_idx_file):
    gene_dict = {}
    FH_GENE = open(gene_idx_file, 'r')
    for line in FH_GENE:
        line_list = line.strip().split('\t')
        gene_dict[line_list[0].strip().upper()] = line_list[1].strip()
    FH_GENE.close()
    return gene_dict


def read_overlap_idx_file(overlap_idx_file):
    overlap_dict = {}
    FH_OVERLAP = open(overlap_idx_file, 'r')
    for line in FH_OVERLAP:
        line_list = line.split('\t')
        gene_ticket = line_list[0].strip()
        if gene_ticket not in overlap_dict:
            overlap_dict[gene_ticket] = []
        overlap_dict[gene_ticket].append([line_list[1].strip(), line_list[2].strip()])
    FH_OVERLAP.close()
    return overlap_dict


def get_curate_status(value_dict):
    curate_status, no_display = '', ''
    if value_dict['Status'] == 'Closed' and value_dict['Resolution'] == 'Complete':
        curate_status = 'Complete'
    elif value_dict['Status'] == 'Closed' and value_dict['Resolution'] == "Won't Fix":
        curate_status = "Gene withdrawn, won't curate"
        no_display = 'none'
    elif value_dict['Status'] == 'Open' or value_dict['Status'] == 'Reopened':
        curate_status = 'Awaiting Review'
    elif value_dict['Status'] == 'Closed' and value_dict['Resolution'] == "Duplicate":
        curate_status = 'duplicate'
    else:
        curate_status = 'unknown'

    return (curate_status, no_display)


def get_gain_score_and_display(value_dict):
    gain_score, gain_score_disp = value_dict['ISCA Triplosensitivity score'], ''
    if gain_score == '3':
        gain_score_disp = 'Sufficient evidence for dosage pathogenicity'
    elif gain_score == '2':
        gain_score_disp = 'Some evidence for dosage pathogenicity'
    elif gain_score == '1':
        gain_score_disp = 'Little evidence for dosage pathogenicity'
    elif gain_score == '0':
        gain_score_disp = 'No evidence for dosage pathogenicity'
    elif gain_score == '40: Dosage sensitivity unlikely':
        gain_score_disp = 'Triplosensitivity unlikely'
        gain_score = 'Triplosensitivity unlikely'
    elif gain_score == 'Not yet evaluated':
        gain_score_disp = gain_score
    elif gain_score == '30: Gene associated with autosomal recessive phenotype':
        gain_score_disp = 'Gene associated with autosomal recessive phenotype'
        gain_score = 'Gene associated with autosomal recessive phenotype'
    else:
        gain_score_disp = 'unknown'

    return (gain_score, gain_score_disp)


def get_loss_score_and_display(value_dict):
    loss_score, loss_score_disp = value_dict['ISCA Haploinsufficiency score'], ''
    if loss_score == '3':
        loss_score_disp = 'Sufficient evidence for dosage pathogenicity'
    elif loss_score == '2':
        loss_score_disp = 'Some evidence for dosage pathogenicity'
    elif loss_score == '1':
        loss_score_disp = 'Little evidence for dosage pathogenicity'
    elif loss_score == '0':
        loss_score_disp = 'No evidence for dosage pathogenicity'
    elif loss_score == '40: Dosage sensitivity unlikely':
        loss_score_disp = 'Haploinsufficiency unlikely'
        loss_score = loss_score_disp
    elif loss_score == 'Not yet evaluated':
        loss_score_disp = loss_score
    elif loss_score == '30: Gene associated with autosomal recessive phenotype':
        loss_score_disp = 'Gene associated with autosomal recessive phenotype'
        loss_score = loss_score_disp
    else:
        loss_score_disp = 'unknown'

    return (loss_score, loss_score_disp)


def get_display_location_and_seqview_location(value_dict, genomic_position_field_key):
    (chrom, chr_start, chr_stop) = ProcessGenomePosition(value_dict[genomic_position_field_key])
    c_start, c_stop, sv_start, sv_stop = '', '', '', ''
    display_loc = ''
    if chr_start != '' and chr_stop != '':
        c_start = '{:,d}'.format(chr_start)
        c_stop = '{:,d}'.format(chr_stop)
        sv_start = chr_start - ((chr_stop - chr_start + 1) * 0.1)
        sv_stop = chr_stop + ((chr_stop - chr_start + 1) * 0.1)
        display_loc = 'chr' + chrom + ': ' + c_start + '-' + c_stop
    if chrom.find('|') != -1:
        chrom = ''

    return (chrom, chr_start, chr_stop, sv_start, sv_stop, display_loc)

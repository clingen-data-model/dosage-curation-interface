#!/usr/bin/python3
import cgi
import cgitb
import sys
import os
import re
from jira.client import JIRA
import isca_me_util
import logging
import logging.config

cgitb.enable()
DIR_NAME = os.path.abspath(os.path.dirname(__file__))
APP_NAME = os.path.splitext(os.path.basename(__file__))[0]


# cgi or command  line run environment
CONFIG = os.path.join(DIR_NAME, 'conf', '.isca_config')
STD_FIELD_FILE = os.path.join(DIR_NAME, 'conf', 'standard_field.ini')

# static files including data file and tempalte file
MIM_FILE = os.path.join(DIR_NAME, 'daily', 'mim_mimnames_cui_gtrname.tsv')
PAGE_TEMPLATE_FILE = os.path.join(DIR_NAME, 'templates/page_tmpl.html')
PRINT_TEMPLATE_FILE = os.path.join(DIR_NAME, 'templates/clingen_print_tmpl.html')
ERROR_TEMPLATE_FILE = os.path.join(DIR_NAME, 'templates/error_tmpl.html')
template_path = os.path.join(DIR_NAME, 'templates')
page_template = isca_me_util.read_file_template(template_path, PAGE_TEMPLATE_FILE)
print_template = isca_me_util.read_file_template(template_path, PRINT_TEMPLATE_FILE)
error_template = isca_me_util.read_file_template(template_path, ERROR_TEMPLATE_FILE)

mim_dict = isca_me_util.read_mim_file(MIM_FILE)

# cgi output header
print("Content-Type: text/html; charset=ISO-8859-1\n")

# cgi id parameter
form = cgi.FieldStorage()
id_param = 'id'
page_param = 'page'
if id_param not in form:
    err_dict = {'error': 'There is a problem with this system ( you entered an invalid paramter )',
                'app_name': APP_NAME, }
    print(error_template.render(err_dict))
    sys.exit(1)

issue_key = form[id_param].value
page_param_val = form[page_param].value if page_param in form else ''

# error dict used for error page template
err_dict = {'error': '',
            'app_name': APP_NAME,
            'key': issue_key}

# connect to NCBI JIRA
try:
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = JIRA(options={'server': 'https://dci.clinicalgenome.org/'},
                basic_auth=(user, passwd))
    if jira is None:
        err_dict['error'] = 'System is down, please try again later'
        print(error_template.render(err_dict))
        sys.exit(1)

except Exception as err:
    err_dict['error'] = str(err)
    print(error_template.render(err_dict))
    sys.exit(1)

# check issue existence
try:
    issue = jira.issue(issue_key)
except Exception as err:
    err_dict['error'] = str(err)
    print(error_template.render(err_dict))
    sys.exit(1)


# Find all values for each field
ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')
used_list = ['Type',
             'Status',
             'Resolution',
             'Updated',
             'Resolved',
             'ISCA Region Name',
             # 'GeneReviews Link',
             'GRCh37 SeqID',
             'GRCh37 Genome Position',
             'GRCh38 SeqID',
             'GRCh38 Genome Position',
             'CytoBand',
             'ISCA Triplosensitivity score',
             'ISCA Haploinsufficiency score',
             'Loss PMID 1',
             'Loss PMID 1 Description',
             'Loss PMID 2',
             'Loss PMID 2 Description',
             'Loss PMID 3',
             'Loss PMID 3 Description',
             'Loss phenotype OMIM ID',
             'Loss phenotype comments',
             'Gain PMID 1',
             'Gain PMID 1 Description',
             'Gain PMID 2',
             'Gain PMID 2 Description',
             'Gain PMID 3',
             'Gain PMID 3 Description',
             'Triplosensitive phenotype OMIM ID',
             'Triplosensitive phenotype comments',
             'Should be targeted?',
             'Targeting decision based on',
             'Targeting decision comment',
             'Loss phenotype ontology identifier',
             'Loss phenotype ontology name',
             'Loss phenotype name',
             'Triplosensitive phenotype ontology identifier',
             'Triplosensitive phenotype ontology name',
             'Triplosensitive phenotype name']
value_dict = isca_me_util.IssueEntries(issue, ISCA_dict, used_list)

# 'GeneReviews Link' may not be avaialbe as field in region ticket
gr = ''
if hasattr(issue.fields, ISCA_dict['GeneReviews Link']):
    if getattr(issue.fields, ISCA_dict['GeneReviews Link']) is not None:
        gr = getattr(issue.fields, ISCA_dict['GeneReviews Link'])

# Type check
if value_dict['Type'] != 'ISCA Region Curation':
    err_dict['error'] = ('Wrong issue type ({}). Please report this '
                         'problem and try another search').format(value_dict['Type'])
    print(error_template.render(err_dict))
    sys.exit(1)


# Curate status
(curate_status, no_display) = isca_me_util.get_curate_status(value_dict)
if curate_status == 'duplicate':
    err_dict['error'] = 'There is a problem with this system ( you entered an invalid region id )'
    print(error_template.render(err_dict))
    sys.exit(1)

# CytoBand
cytoband = value_dict['CytoBand']
if cytoband == 'NA':
    cytoband = 'No cytogenetic data available'

# location
(chrom, chr_start, chr_stop,
 sv_start, sv_stop,
 display_loc) = isca_me_util.get_display_location_and_seqview_location(
    value_dict, 'GRCh37 Genome Position')

(GRCh38_chrom, GRCh38_chr_start, GRCh38_chr_stop,
 GRCh38_sv_start, GRCh38_sv_stop,
 GRCh38_display_loc) = isca_me_util.get_display_location_and_seqview_location(
    value_dict, 'GRCh38 Genome Position')

# Gain/Loss Field
(gain_score, gain_score_disp) = isca_me_util.get_gain_score_and_display(value_dict)
(loss_score, loss_score_disp) = isca_me_util.get_loss_score_and_display(value_dict)

# target
target_str = value_dict['Should be targeted?']
if target_str.startswith('Target'):
    target_str = 'Target'

# PMID
loss_pm1 = isca_me_util.CleanPMID(value_dict['Loss PMID 1'])
loss_pm2 = isca_me_util.CleanPMID(value_dict['Loss PMID 2'])
loss_pm3 = isca_me_util.CleanPMID(value_dict['Loss PMID 3'])
gain_pm1 = isca_me_util.CleanPMID(value_dict['Gain PMID 1'])
gain_pm2 = isca_me_util.CleanPMID(value_dict['Gain PMID 2'])
gain_pm3 = isca_me_util.CleanPMID(value_dict['Gain PMID 3'])

# pheno_description
loss_pheno_omim_dict, gain_pheno_omim_dict = {}, {}
temp_loss_omim_list = isca_me_util.CleanOMIM(value_dict['Loss phenotype OMIM ID'])
for item in temp_loss_omim_list:
    if item in mim_dict:
        loss_pheno_omim_dict[item] = mim_dict[item]

gain_pheno_desc, gain_pheno_omim = [], []
temp_gain_omim_list = isca_me_util.CleanOMIM(value_dict['Triplosensitive phenotype OMIM ID'])
for item in temp_gain_omim_list:
    if item in mim_dict:
        gain_pheno_omim_dict[item] = mim_dict[item]

# ontology
(gain_ontology_type_name, gain_ontology_id, gain_ontology_id_prefix,
 gain_ontology_base_url) = isca_me_util.CleanOntology(
    value_dict['Triplosensitive phenotype ontology name'],
    value_dict['Triplosensitive phenotype ontology identifier'])
(loss_ontology_type_name, loss_ontology_id, loss_ontology_id_prefix,
 loss_ontology_base_url) = isca_me_util.CleanOntology(
    value_dict['Loss phenotype ontology name'],
    value_dict['Loss phenotype ontology identifier'])

# resolution date
resolution_date = (value_dict['Resolved'].split('T')[0].strip()
                   if value_dict['Resolved'] != '' else '')

c = {
     'key': issue.key,
     'type': '',  # for gene curation page
     'iss_type': value_dict['Type'],
     'no_display': no_display,
     'region_name': value_dict['ISCA Region Name'],
     'gene_omim': '',  # for gene curation page
     'curate_status': curate_status,
     'gr': gr,
     'cytoband': cytoband,
     'loc': display_loc,
     'chrom': chrom,
     'chr_start': chr_start,
     'chr_stop': chr_stop,
     'sv_start': sv_start,
     'sv_stop': sv_stop,
     'seqID': value_dict['GRCh37 SeqID'],

     'GRCh38_loc': GRCh38_display_loc,
     'GRCh38_chrom': GRCh38_chrom,
     'GRCh38_chr_start': GRCh38_chr_start,
     'GRCh38_chr_stop': GRCh38_chr_stop,
     'GRCh38_sv_start': GRCh38_sv_start,
     'GRCh38_sv_stop': GRCh38_sv_stop,
     'GRCh38_seqID': value_dict['GRCh38 SeqID'],

     'targ_dec': target_str,
     'reason': value_dict['Targeting decision based on'],
     'rec_comments': value_dict['Targeting decision comment'],
     'update': value_dict['Updated'].split('T')[0].strip(),
     'resolutiondate': resolution_date,
     'l_pm1': loss_pm1,
     'l_pm1_com': value_dict['Loss PMID 1 Description'],
     'l_pm2': loss_pm2,
     'l_pm2_com': value_dict['Loss PMID 2 Description'],
     'l_pm3': loss_pm3,
     'l_pm3_com': value_dict['Loss PMID 3 Description'],
     'loss_phen_dict': loss_pheno_omim_dict,
     'loss_pheno_com': value_dict['Loss phenotype comments'],
     'loss_score': loss_score,
     'loss_score_disp': loss_score_disp,
     'g_pm1': gain_pm1,
     'g_pm1_com': value_dict['Gain PMID 1 Description'],
     'g_pm2': gain_pm2,
     'g_pm2_com': value_dict['Gain PMID 2 Description'],
     'g_pm3': gain_pm3,
     'g_pm3_com': value_dict['Gain PMID 3 Description'],
     'gain_phen_dict': gain_pheno_omim_dict,
     'gain_pheno_com': value_dict['Triplosensitive phenotype comments'],
     'gain_score': gain_score,
     'gain_score_disp': gain_score_disp,
     'app_name': APP_NAME,
     'gain_ontology_type_name':  gain_ontology_type_name,
     'gain_ontology_id':  gain_ontology_id,
     'gain_ontology_id_prefix':  gain_ontology_id_prefix,
     'gain_ontology_base_url':  gain_ontology_base_url,
     'gain_phenotype_name':  value_dict['Triplosensitive phenotype name'],
     'loss_ontology_type_name':  loss_ontology_type_name,
     'loss_ontology_id':  loss_ontology_id,
     'loss_ontology_id_prefix':  loss_ontology_id_prefix,
     'loss_ontology_base_url':  loss_ontology_base_url,
     'loss_phenotype_name':  value_dict['Loss phenotype name']
}

check_list = ['g_pm1_com',
              'g_pm2_com',
              'g_pm3_com',
              'l_pm1_com',
              'l_pm2_com',
              'l_pm3_com',
              'gain_pheno_com',
              'loss_pheno_com',
              'rec_comments']

# utf-8 display issues for jinja2, currently just convert it to "?" temporarily
for k in c.keys():
    if k in check_list:
        if c[k] is None or c[k] == "":
            continue
        if re.match(r'^[\x00-\x7F]+$', c[k]) is None:
            c[k] = re.sub(r'[^\x00-\x7F]+', '?', c[k])


if page_param_val == 'print':
    print(print_template.render(c))
else:
    print(page_template.render(c))

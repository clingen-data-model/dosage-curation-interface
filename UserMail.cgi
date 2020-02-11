#!/usr/bin/python3
import cgi
import cgitb
import os
import sys
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
template_path = os.path.join(DIR_NAME, 'templates')
RECEIPT_TEMPLATE_FILE = 'receipt_tmpl.html'
ERROR_TEMPLATE_FILE = 'error_tmpl.html'
receipt_template = isca_me_util.read_file_template(template_path, RECEIPT_TEMPLATE_FILE)
error_template = isca_me_util.read_file_template(template_path, ERROR_TEMPLATE_FILE)


# cgi output header
print("Content-Type: text/html; charset=ISO-8859-1\n")

# cgi  parameters
form = cgi.FieldStorage()
gene_sym_param, gene_loc_param = 'gene', 'loc'
email_param, desc_param = 'email', 'message'
subject_param = 'subject'

gene_sym_param_val = form[gene_sym_param].value if gene_sym_param in form else 'not provided'
gene_loc_param_val = form[gene_loc_param].value if gene_loc_param in form else 'not provided'
subject_param_val = form[subject_param].value if subject_param in form else ''
desc_param_val = form[desc_param].value if desc_param in form else ''
email_param_val = form[email_param].value if email_param in form else ''

if desc_param_val == '':
    err_dict = {'error': ('Missing field: There is no message. Please go back to the '
                          'contact page and provide more details.<br />'),
                'app_name': APP_NAME,
                'sym': ''}
    print(error_template.render(err_dict))
    sys.exit(1)

# error dict used for error page template
err_dict = {'error': '',
            'app_name': APP_NAME,
            'sym': ''}

if subject_param_val != '':
    err_dict['error'] = 'Potential Bot attack'
    print(error_template.render(err_dict))
    sys.exit(1)

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

issue_dict = {
    'project': {'key': 'EBRM'},
    'summary': 'Request from external user.',
    'description': desc_param_val,
    'issuetype': {'name': 'Web'},
    'customfield_10030': gene_sym_param_val,
    'customfield_10160': gene_loc_param_val,
    'customfield_10011': email_param_val
}

try:
    new_issue = jira.create_issue(fields=issue_dict)
    c = {
         'key': new_issue.key,
         'sym': gene_sym_param_val,
         'sub_loc': gene_loc_param_val,
         'app_name': APP_NAME}
    print(receipt_template.render(c))
except Exception as err:
    err_dict['error'] = ('<br />Issue not created. There is a problem with our database, '
                         'please try again later.\n' + str(err))
    print(error_template.render(err_dict))
    sys.exit(1)

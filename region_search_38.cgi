#!/usr/bin/python3
import cgi
import cgitb
import os
import sys
import re
import isca_me_util

cgitb.enable()
DIR_NAME = os.path.abspath(os.path.dirname(__file__))
APP_NAME = os.path.splitext(os.path.basename(__file__))[0]

CONFIG = os.path.join(DIR_NAME, 'conf', '.isca_config')
STD_FIELD_FILE = os.path.join(DIR_NAME, 'conf', 'standard_field.ini')

# static files including data file and tempalte file
GENE_IDX_FILE = os.path.join(DIR_NAME, 'daily', 'gene_isca.idx')
REGION_IDX_FILE = os.path.join(DIR_NAME, 'daily', 'region38.idx')
RESULT_TEMPLATE_FILE = 'result_tmpl_38.html'
ERROR_TEMPLATE_FILE = 'error_tmpl.html'
template_path = os.path.join(DIR_NAME, 'templates')
result_template = isca_me_util.read_file_template(template_path, RESULT_TEMPLATE_FILE)
error_template = isca_me_util.read_file_template(template_path, ERROR_TEMPLATE_FILE)

#READ static FILE
gene_dict={}
FH_GENE=open(GENE_IDX_FILE,'r')
for line in FH_GENE:
    line_list = line.strip().split('\t')
    gene_dict[line_list[1].strip()] = line_list[0].strip()
FH_GENE.close()

# cgi output header
print("Content-Type: text/html; charset=ISO-8859-1\n")

# Get cgi parameter
form = cgi.FieldStorage()
loc_param = 'loc'
if loc_param not in form:
    err_dict = {'error': ('There is a problem with this system or '
                          'you entered an invalid search location'),
                'app_name': APP_NAME, }
    print(error_template.render(err_dict))
    sys.exit(1)

sub_loc = "".join(form[loc_param].value.upper().split())  # to upper and remove white space

# error dict used for error page template
err_dict = {'error': ('There is a problem with this system or '
                      'you entered an invalid search location'),
            'app_name': APP_NAME,
            'sub_loc': form[loc_param].value}

# check sub_loc validity
pattern = """
    ^                     # begin
    (CHR)?                # optional chr
    (1?[0-9]|2[0-2]|X|Y)  # 1-22 or x, y
    :                     # comma
    (\d{1,3}(,?\d{3})*)   # start
    -                     # hyphen
    (\d{1,3}(,?\d{3})*)   # stop
    $                     # end
"""
search_res = re.search(pattern, sub_loc, re.VERBOSE)
if search_res is None:
    err_dict['error'] = ('There is a problem with this system or you '
                         'entered an invalid search location, Please use chr:start-stop')
    print(error_template.render(err_dict))
    sys.exit(1)

# print >>sys.stderr, search_res.groups()
sub_chr = 'CHR' + search_res.group(2)
sub_start = int(search_res.group(3).replace(',', ''))
sub_stop = int(search_res.group(5).replace(',', ''))
if sub_start > sub_stop:
    err_dict['error'] = 'Start is greater than stop. Please enter a valid location.'
    print(error_template.render(err_dict))
    sys.exit(1)

gene_hits, region_hits = [], []
# search through sorted region.idx file
FH_REGION = open(REGION_IDX_FILE, 'r')
for line in FH_REGION:
    if len(line) == 0 or line.startswith('#'):
        continue
    line_list = line.split('\t')
    chr_loc = line_list[0].strip()
    id = line_list[1].strip()
    type = line_list[2].strip()
    cur_stat = line_list[3].strip()
    reg_name = line_list[4].strip()
    gain_score = line_list[5].strip()
    loss_score = line_list[6].strip()
    pli = line_list[7].strip()
    omim = line_list[8].strip()
    # chr_loc on ALT/PATCH
    if chr_loc.find(':') == -1:
        continue

    # get region/gene location
    chr_loc_list = chr_loc.split(':')
    chr = chr_loc_list[0].strip().upper()  # upper case
    loc_str_list = chr_loc_list[1].strip().split('-')
    start = int(loc_str_list[0].strip().replace(',', ''))
    stop = int(loc_str_list[1].strip().replace(',', ''))

    if chr == sub_chr:
        if start <= sub_stop and stop >= sub_start:
            # generatl overlap

            # url and gene symbol
            url, gene = '', ''
            if type == 'ISCA Region Curation':
                url = 'clingen_region.cgi?id=' + id
                gene = 'NA'
            else:
                url = 'clingen_gene.cgi?sym=' + gene_dict[id]
                gene = gene_dict[id]

            # overlap type
            overlap_type = 'Overlap'
            if start >= sub_start and stop <= sub_stop:  # contained
                overlap_type = 'Contained'

            # record dict
            rec = {
                'id': id,
                'LOC': chr.lower() + ':' + '{:,d}'.format(start) + '-' + '{:,d}'.format(stop),
                'type': type,
                'LO': url,
                'GENE': gene,
                'CUR_STAT': cur_stat,
                'OL':  overlap_type,
                'NAME':  reg_name,
                'GAIN_SCORE': gain_score,
                'LOSS_SCORE': loss_score,
                'PLI': pli,
                'OMIM': omim,
            }

            if type == 'ISCA Gene Curation':
                gene_hits.append(rec)
            else:
                region_hits.append(rec)

FH_REGION.close()
c = {
    'sub_loc': (sub_chr.lower() + ':' + '{:,d}'.format(sub_start) +
                '-' + '{:,d}'.format(sub_stop)),
    'gene_hits': gene_hits,
    'reg_hits': region_hits,
    'reg_hit_disp': len(region_hits),
    'gene_hit_disp': len(gene_hits),
    'region_ct': len(region_hits),
    'gene_ct': len(gene_hits),
    'app_name': APP_NAME,
    'sub_chr': sub_chr.lower(),
    'sub_pos': str(sub_start) + '-' + str(sub_stop)}

print(result_template.render(c))

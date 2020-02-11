#!/usr/bin/python3
import cgi
import cgitb
import smtplib
from email.mime.text import MIMEText
import sys


cgitb.enable()
# cgi output header
print("Content-Type: text/html; charset=ISO-8859-1\n")


# cgi parameter
form = cgi.FieldStorage()

# cgi  parameters
form = cgi.FieldStorage()
sym_param, page_param = 'sym', 'page'
out_param, subject_param = 'out', 'subject'

email_param, name_param = 'email', 'userName'
key_param, user_comment_param = 'key', 'userComment'
dos_group1_param, pmid1_param, pmid1_desc_param = 'dos_group1', 'pmid1', 'pmid1_desc'
dos_group2_param, pmid2_param, pmid2_desc_param = 'dos_group2', 'pmid2', 'pmid2_desc'
dos_group3_param, pmid3_param, pmid3_desc_param = 'dos_group3', 'pmid3', 'pmid3_desc'
subject_param = 'subject'

email_val = form[email_param].value if email_param in form else ''
name_val = form[name_param].value if name_param in form else ''
key_val = form[key_param].value if key_param in form else ''
user_comment_val = form[user_comment_param].value if user_comment_param in form else ''
dos_group1_val = form[dos_group1_param].value if dos_group1_param in form else ''
dos_group2_val = form[dos_group2_param].value if dos_group2_param in form else ''
dos_group3_val = form[dos_group3_param].value if dos_group3_param in form else ''
pmid1_val = form[pmid1_param].value if pmid1_param in form else ''
pmid2_val = form[pmid2_param].value if pmid2_param in form else ''
pmid3_val = form[pmid3_param].value if pmid3_param in form else ''
pmid1_desc_val = form[pmid1_desc_param].value if pmid1_desc_param in form else ''
pmid2_desc_val = form[pmid2_desc_param].value if pmid2_desc_param in form else ''
pmid3_desc_val = form[pmid3_desc_param].value if pmid3_desc_param in form else ''
subject_val = form[subject_param].value if subject_param in form else ''


error = ''
if name_val == '':
    error += 'Missing field: We need a name so we can contact you..<br />'
if email_val == '':
    error += 'Missing field: We need an email to contact you. <br/>'
if pmid1_val == '':
    error += 'Missing field: We need at least 1 pmid. <br/>'
if subject_val != '':
    error += 'Possible bot attack: hidden field populated.'

if error != '':
    print("<p>We are sorry. There was a problem with your submission:</p>")
    print(" <p>" + error + "</p>")
    sys.exit(1)


content = 'key: ' + key_val + '\n'
content += 'email: ' + email_val + '\n'
content += 'name: ' + name_val + '\n'
content += '\nuserComment: ' + user_comment_val + '\n'
content += '\nsubmission 1: ' + dos_group1_val + '\n'
content += 'PMID1: ' + pmid1_val + '\n'
content += 'Description PMID1: ' + pmid1_desc_val + '\n'
content += '\nsubmission 2: ' + dos_group2_val + '\n'
content += 'PMID2: ' + pmid2_val + '\n'
content += 'Description PMID2: ' + pmid2_desc_val + '\n'
content += '\nsubmission 3: ' + dos_group3_val + '\n'
content += 'PMID3: ' + pmid3_val + '\n'
content += 'Description PMID3: ' + pmid3_desc_val + '\n'

me = 'dci-support@ne.clinicalgenome.org'
recipients = ['pweller1@geisinger.edu', 'eriggs@geisinger.edu']


msg = MIMEText(content)
msg['Subject'] = 'ClinGen User Submission for ' + key_val
msg['From'] = me
msg['To'] = ", ".join(recipients)
s = smtplib.SMTP('localhost')
s.sendmail(me, recipients, msg.as_string())
s.quit()

print("<h2>Thank you for submitting information</h2>\n")

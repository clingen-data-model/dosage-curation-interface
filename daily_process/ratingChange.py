"""
     Genreate ratingchange.html, which contain tickets with label of RatingChange
"""
import os
import sys
import time
import isca_me_util
from datetime import datetime


# config file
DATA_DIR = '../conf'
CONFIG = os.path.join(DATA_DIR, '.isca_config')
STD_FIELD_FILE = os.path.join(DATA_DIR, 'standard_field.ini')
RATINGCHANGE_HTML = 'ratingchange.html'


def GetIssuesByJQLExpand(jira, JQL_statement, FH_LOG=sys.stderr, p_expand=None):
    """ return the issue list related to search of JQL_statement """
    try:
        MAX_RESULT = 500
        issue_list = []
        start_at = 0
        t0 = time.time()
        while True:
            current_result = jira.search_issues(JQL_statement, startAt=start_at,
                                                maxResults=MAX_RESULT, expand=p_expand)
            issue_list += current_result
            print("Begin to get result, start_at %d ticket with execution_time %.3f" % (
                start_at, round(time.time() - t0, 3)),
                  file=FH_LOG)
            if len(current_result) < MAX_RESULT:
                break
            else:
                start_at += MAX_RESULT
        print("final result, start_at %d ticket with execution_time %.3f" % (
            start_at, round(time.time() - t0, 3)),
              file=FH_LOG)
        print("there are already %d tickets returned" % (len(issue_list)),
              file=FH_LOG)
    except Exception as inst:
        print(type(inst), file=FH_LOG)
        print(str(inst), file=FH_LOG)
        sys.exit(1)

    return issue_list


def printRow(FILE_HANDLE, href_prefix, name, score_type, from_score, to_score, date_value):
    date_list = date_value.split('T')[0].split('-')
    ret_date = '/'.join([date_list[1], date_list[2], date_list[0]])
    ret_list = []
    ret_list.append("\t<tr>\n\t<td><a href=\"%s\" target=\"_blank\">%s</a></td>" % (
        href_prefix, name))
    ret_list.append("\t<td class=\"score_col\">%s: %s</td>" % (score_type, from_score))
    ret_list.append("\t<td class=\"score_col\">%s: %s</td>" % (score_type, to_score))
    ret_list.append("\t<td>%s</td>\n\t</tr>" % (ret_date))
    return ret_list


def rateChange_13_week(history_change_date, curr_date):
    change_time = datetime.strptime(history_change_date, "%Y-%m-%dT%H:%M:%S")
    time_diff = (curr_date - change_time).days
    return (1 if time_diff <= 13 * 7 else 0)


if __name__ == "__main__":
    FH_HTML = open(RATINGCHANGE_HTML, 'w')
    print("<h3>Genes/Regions with Updated Scores</h3>", file=FH_HTML)

    table_prefix_list = []
    table_prefix_list.append("<table data-jig=\"ncbigrid\">")
    table_prefix_list.append("\t<thead>\n\t<tr>")
    table_prefix_list.append("\t<th>Gene/Region Name</th>")
    table_prefix_list.append("\t<th class=\"score_col\">Old score</th>")
    table_prefix_list.append("\t<th class=\"score_col\">New score</th>")
    table_prefix_list.append("\t<th>Date changed</th>")
    table_prefix_list.append("\t</tr>\n\t</thead>")
    table_prefix_list.append("\t<tbody>")

    curr_datetime = datetime.now()
    (user, passwd) = isca_me_util.ParseLoginConfig(CONFIG)
    jira = isca_me_util.JiraConnect(user, passwd)
    ISCA_dict = isca_me_util.GetFieldDict(STD_FIELD_FILE, 'ISCA')

    query_str = ("project = ISCA AND issuetype in "
                 "(\"ISCA Gene Curation\", \"ISCA Region Curation\") "
                 "AND labels in (\"RatingChange\")")
    issue_list = GetIssuesByJQLExpand(jira, query_str, sys.stdout, p_expand='changelog')

    change_cnt = 0
    list_str = []
    for issue in issue_list:

        # first columan name (genesymbol or region_name)
        name, href_prefix = '', ''
        issue_type = getattr(issue.fields, ISCA_dict['Type']).name.strip()
        if issue_type == 'ISCA Gene Curation':
            name = getattr(issue.fields, ISCA_dict['Gene Symbol']).strip()
            href_prefix = 'clingen_gene.cgi?sym=' + name
        elif issue_type == 'ISCA Region Curation':
            name = getattr(issue.fields, ISCA_dict['ISCA Region Name']).strip()
            href_prefix = 'clingen_region.cgi?id=' + issue.key

        # changelog history
        gain_list, loss_list = [], []
        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == 'ISCA Triplosensitivity score':
                    if (item.fromString is not None
                            and item.fromString.strip() != 'Not yet evaluated'
                            and item.toString is not None):
                        gain_list.append([issue.key, history.created,
                                          item.fromString, item.toString])

                if item.field == 'ISCA Haploinsufficiency score':
                    if (item.fromString is not None
                            and item.fromString.strip() != 'Not yet evaluated'
                            and item.toString is not None):
                        loss_list.append([issue.key, history.created,
                                          item.fromString, item.toString])

        # print the latest change if available
        if len(gain_list) > 0:
            bool_ret = rateChange_13_week(gain_list[-1][1][:19], curr_datetime)
            if bool_ret:
                change_cnt += 1
                ret_list = printRow(FH_HTML, href_prefix, name, 'Triplosensitivity score',
                                    gain_list[-1][2], gain_list[-1][3], gain_list[-1][1])
                list_str.extend(ret_list)
        if len(loss_list) > 0:
            bool_ret = rateChange_13_week(loss_list[-1][1][:19], curr_datetime)
            if bool_ret:
                change_cnt += 1
                ret_list = printRow(FH_HTML, href_prefix, name, 'Haploinsufficiency score',
                                    loss_list[-1][2], loss_list[-1][3], loss_list[-1][1])
                list_str.extend(ret_list)

    if change_cnt > 0:
        for item in table_prefix_list:
            print(item, file=FH_HTML)
        for item in list_str:
            print(item, file=FH_HTML)
        print("\t</tbody>", file=FH_HTML)
        print("</table>", file=FH_HTML)
    else:
        print('<p>No scores were updated in the last 13 weeks</p>', file=FH_HTML)
    FH_HTML.close()

import re
import sys
from invenio.search_engine import perform_request_search
from invenio.search_engine import get_fieldvalues
#from hep_convert_email_to_id import get_hepnames_recid_from_email
from hep_convert_email_to_id import find_inspire_id_from_record
from invenio.search_engine import search_unit
from invenio.intbitset import intbitset

"""
Looks for problems with INSPIRE-IDs in HEPNames
"""

VERBOSE = False
VERBOSE = True
#LETTER = 'U'

def main():
    filename = 'tmp_' + __file__
    filename = re.sub('.py', '_correct.out', filename)
    output = open(filename,'w')
    sys.stdout = output
    hepnames_search_ids()
    output.close()

def hepnames_search_ids():
#    name_letter = letter + '*'
    id_search = '035__9:bai or 035__9:inspire'
    id_search += ' or 035__9:orcid or 035__9:jacow'
    field_search = ['035__a', id_search, 'HepNames']
    examine(field_search)

def examine(field_search):
    field = field_search[0]
    search = field_search[1]
    collection = field_search[2]
    if not re.search(r'\:', search):
        search = field + ':' + search
    result = perform_request_search(p = search, cc = collection)
    if VERBOSE:
        print 'VERBOSE', field, search, collection, len(result)
    already_seen_field_values = []
    for recid in result:
        recid_print = ""
        field_values = get_fieldvalues(recid, field)
        for field_value in field_values:
            bad_id = False
            if field_value in already_seen_field_values:
                continue
            if re.search(r'INSPIRE', field_value):
                inspire_form = r'^INSPIRE-\d{8}$'
                if not re.match(inspire_form, field_value):
                    print 'Bad INSPIRE ID: ', field_value
                    bad_id = True
            elif re.search(r'^0000-', field_value):
                orcid_form = r'^0000-\d{4}-\d{4}-\d{3}[\dX]$'
                if not re.match(orcid_form, field_value):
                    print 'Bad ORCID ID: ', field_value
                    bad_id = True
            search_dup = '{0}:"{1}"'.format(field, field_value)

            if field_value in already_seen_field_values:
                continue
            result_dup =  perform_request_search(p = search_dup, \
                              cc = 'HepNames')
            if len(result_dup) != 1 or bad_id:
                if len(result_dup) == 0:
                    print_field_value = field_value
                    print '{0:40s} {1:30s}'. \
                          format(print_field_value, recid_print)
                else:
                    print search_dup, recid_print, result_dup, bad_id
            already_seen_field_values.append(field_value)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print 'Exiting'


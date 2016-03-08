#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import cgi
import sys

from invenio.search_engine import perform_request_search
from invenio.search_engine import get_fieldvalues
from invenio.search_engine import print_record
from invenio.bibrecord import print_rec, record_add_field

VERBOSE = True
VERBOSE = False
RECIDS = []

def find_recid(id):
    id = re.sub(r';', '', id)
    if id.isdigit():
        #print "Invalid ID: " , id
        #return False
        search = "001:" + id + " or 970__a:SPIRES-" + id + " 037:FERMILAB*"        
    elif re.search(r'FERMILAB', id):
        id = re.sub(r'\/', '-', id)
        search = "037:" + id
    elif re.search(r'10\.\d+\/', id):
        search = "0247_a:" + id
    x = perform_request_search(p = search, cc = 'HEP')
    if len(x) == 1:
        recid = x[0]
        if recid in RECIDS:
            return False
        else:
            RECIDS.append(recid)
            return recid
    else:
        return False

def add_osti_id(string):
    if re.search(r'\s*Video\s*NA\s*NA', string):
        return False
    elif re.search(r'duplicat[eion]+ of OSTI ID', string):    
        return False
    elif re.search(r'\tSoftware\t', string):
        return False
    match_obj_1 = re.match(r'^\s*(\d+)\s+(\d+)', string)
    match_obj_2 = re.match(r'^\s*(\d+).*(FERMILAB[\-A-z0-9\/]+)', string)
    match_obj_3 = re.match(r'^\s*(\d+).*(10\.\d+\/\S+)', string)
    
    if match_obj_1:
        id_1 = match_obj_1.group(1)
        id_2 = match_obj_1.group(2)
        recid_guess_1 = find_recid(id_1)
        recid_guess_2 = find_recid(id_2)
        if recid_guess_1:
            recid = recid_guess_1
            osti_id = id_2
        elif recid_guess_2:
            recid = recid_guess_2
            osti_id = id_1
    elif match_obj_2:
        osti_id = match_obj_2.group(1) 
        report_num = match_obj_2.group(2)
        recid = find_recid(report_num)
    elif match_obj_3:
        osti_id = match_obj_3.group(1)
        doi = match_obj_3.group(2)
        recid = find_recid(doi)
    else:
        print "Cannot find valid ID:", string
        return False
    if not recid:
        print "Cannot find valid recid:", string
        return False
    search = "001:" + str(recid) + " -035__9:OSTI"
    if VERBOSE:
        print search
    result = perform_request_search(p = search, cc = 'HEP')
    if not len(result) == 1:
        return False   
    if VERBOSE:
        print result
    record = {}
    record_add_field(record, '001', controlfield_value=str(recid))
    new_id  = [('a', osti_id), ('9', 'OSTI')]
    record_add_field(record, '035', '', '', subfields=new_id)
    try:
        return print_rec(record)
    except:
        print "Something wrong: " + search                    
        return False

def main(input):
    filename = 'tmp_' + __file__
    filename = re.sub('.py', '_append.out', filename)
    output = open(filename,'w')
    output.write('<collection>')
    if input:
        output_data = add_osti_id(input)
        if output_data:
            output.write(output_data)
    else:
        try:
            for i in open('osti.in','r').readlines():
                output_data = add_osti_id(i)
                if output_data:
                    output.write(output_data)
        except IOError as e:
            print "An error\n"
            print("({})".format(e))
    output.write('</collection>')
    output.close()


if __name__ == '__main__':
    search = sys.argv
    try:
        if len(search) == 1 :
            main(0)
        elif len(search) == 2:
            search = search[1:][0]
            main(search)
    except KeyboardInterrupt:
        print 'Exiting'
    

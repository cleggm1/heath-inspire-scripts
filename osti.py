#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import cgi
import sys    
    
from invenio.search_engine import perform_request_search
from invenio.search_engine import get_fieldvalues
from invenio.search_engine import print_record
from invenio.intbitset import intbitset
from check_url import checkURL
    
def main(search):
    if not search:
        search = "find r fermilab and dadd 2014"
    print search
    search_original = search
    x = intbitset(perform_request_search(p=search, cc='HEP'))    
    print len(x)
    fermilab         = intbitset(perform_request_search(p="8564_y:fermilab*", cc='HEP'))
    fermilabtoday   = intbitset(perform_request_search(p="8564_y:fermilabtoday", cc='HEP'))
    fermilabpub     = intbitset(perform_request_search(p="8564_y:fermilabpub", cc='HEP'))
    fermilabthesis  = intbitset(perform_request_search(p="8564_y:fermilabthesis", cc='HEP'))
    fermilabconf    = intbitset(perform_request_search(p="8564_y:fermilabconf", cc='HEP'))
    fermilabtm      = intbitset(perform_request_search(p="8564_y:fermilabtm", cc='HEP'))
    ok = fermilab - fermilabtoday | fermilabpub | fermilabthesis | fermilabconf | fermilabtm
    print len(ok)
    x = x & ok
    print len(x)    
    
    fileName    = 'osti.out'
    fileName2 = 'osti2.out'
    output = open(fileName, 'w')
    output.write("<harvest-site>\n")
    for r in x:
            output.write(print_record(r, format='xsti'))
    output.write("</harvest-site>\n")
    output.close()
    
    
    output2 = open(fileName2, 'w')
    #noUrl = False
    #arXiv_flag = False
    subj_category_flag = False
    subj_keywords_flag = False
    url_check_flag = True
    url_check_flag = False
    counter = 1

    for i in open(fileName, 'r'): 
        issue = None
        i = re.sub(r'(find_paper\.pl\?[\w\-]+)', r'\1.pdf', i)
        i = re.sub(r'pdf\.pdf', 'pdf', i)
        i = re.sub(r'shtml\.pdf', 'shtml', i)
    
        if re.search(r'accession_num', i):
            matchObj = re.match(r'.*<accession_num>(\d+)</accession_num>.*', i)
            if matchObj: 
                accession_num = matchObj.group(1)
                search = "find recid " + accession_num + " or irn " + accession_num + " and r fermilab"
                y = perform_request_search(p=search, cc='HEP')
                if len(y) == 1 : recid = y[0]
                #print("{0} {1} {2}".format(counter, accession_num, recid))
                counter += 1    

                authors = get_fieldvalues(recid, '700__a')
                if len(authors) > 9 : 
                    author = get_fieldvalues(recid, '100__a')[0]
                    author = "    <author>" + author + "; et al.</author>\n"
                    i = i + author
                    collaboration = get_fieldvalues(recid, '710__g')
                    if collaboration:
                        collaboration = cgi.escape(collaboration[0])
                        collaboration = "    <contributor_organizations>" + collaboration + "</contributor_organizations>\n"
                        i = i + collaboration
    
                search = "001:" + str(recid) + " 8564_y:FERMILAB*"
                #search = "001:" + str(recid) + " 037__9:arXiv"
                z = perform_request_search(p=search, cc='HEP')
                if len(z) < 1 : 
                  noUrl = True             
                  print 'No url for ', recid
                  break
                #if len(z) == 1 : arXiv_flag = True
                #else : arXiv_flag = False

                phd_date = get_fieldvalues(recid, '502__d')
                normal_date = get_fieldvalues(recid, '269__c')
                if phd_date and not normal_date: 
                    phd_date = "    <date>" + phd_date[0] + "</date>\n"
                    i = i + phd_date

        #if arXiv_flag and re.search("<availability>http://arXiv.org", i) :
        #    url = i
        #    url = re.sub(r'availability', 'url', url)
        #    url = re.sub(r'arXiv.org/abs', 'arXiv.org/pdf', url)
        #    i = i + url
        #    #noUrl = False
        if re.search("<url>", i):
            #if arXiv_flag : i = ''            
            if re.search("www.fnal.gov/pub/today", i) : i = ''
            elif re.search("<url>.*fnal", i) :
                matchObj = re.match(r'.*<url>(.*fnal.*)</url>.*', i)
                if matchObj:
                    url_to_check =    matchObj.group(1)
                    if re.search("shtml", url_to_check) :
                        url_to_check = re.sub(r'.*fermilab\-(.*)\.shtml', r'http://lss.fnal.gov/cgi-bin/find_paper.pl?\1.pdf', url_to_check)
                        if url_check_flag:
                            if not checkURL(url_to_check) :
                                error_message = "Something wrong with " + url_to_check
                                print error_message
                                break
                            else : print "No problem with url: ", url_to_check
                    i = "  <url>" + url_to_check + "</url>\n"                        
            else : i = ''
    
        if re.search("<title>", i) :
            title = get_fieldvalues(recid, '245__a')[0]
            title = cgi.escape(title)
            i = "  <title>" + title + "</title>\n"

        if re.search("<date>", i) :
            if re.search(">\d\d\d\d\-\d\d\-\d\d<", i) :
              i = re.sub(r'>(\d\d\d\d)\-(\d\d)\-(\d\d)<', r'>\2/\3/\1<', i)
            elif re.search(">\d\d\d\d\-\d\d<", i) :
              i = re.sub(r'>(\d\d\d\d)\-(\d\d)<', r'>\2/01/\1<', i)
            elif re.search(">\d\d\d\d<", i) :
              i = re.sub(r'>(\d\d\d\d)<', r'>01/01/\1<', i)
            else : 
                print "Bad date: ", recid, i
                break
            abstract = get_fieldvalues(recid, '520__a')
            if abstract : 
                abstract = abstract[0]
                abstract = cgi.escape(abstract)
                abstract = "  <abstract>" + abstract + "</abstract>\n"
                i = i + abstract
    
        if re.search("journal", i) :
            i = re.sub(r'<journal_info>(.*[ \.])(\S+)\:(\S+)\,(\d+)</journal_info>', r'<journal_name>\1</journal_name>\n    <journal_volume>\2</journal_volume>\n    <journal_issue></journal_issue>', i)
            issue = get_fieldvalues(recid, '773__n')
            if issue : 
                issue = issue[0]
                issue = "<journal_issue>" + str(issue) + "</journal_issue>"
                i = re.sub(r'<journal_issue></journal_issue>', issue, i)
    
        if re.search("<sponsor_org>", i) : 
            i = re.sub(r'DOE Office of Science', r'USDOE Office of Science (SC), High Energy Physics (HEP) (SC-25)', i)

        if re.search("<subj_category>", i) : 
            if subj_category_flag : i = ''
            subj_category_flag = True

        if re.search("<subj_keywords>", i) :
            if subj_keywords_flag : i = ''
            subj_keywords_flag = True
   
        if i : output2.write(i)
        
    output2.close()
    print search_original    

if __name__ == '__main__':
    search = sys.argv[1:][0]
    try:
        main(search)
    except KeyboardInterrupt:
        print 'Exiting'


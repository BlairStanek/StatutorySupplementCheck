# Created 15 Dec 2021 by Andrew Blair-Stanek to handle checking
# on the Treas Reg portions of the Code & Regs.

import xml.etree.ElementTree as ET
import os
import re

import utils


# Gets all non-header text from NON-repealed sections
def get_TR_text_recursive(x:ET.Element) -> str:
    if x.tag in ["SECTNO", "SUBJECT", "CITA"]:
        return ""

    rv = ""
    if x.text is not None:
        rv += x.text + " "
    for sub in x:
        rv += get_TR_text_recursive(sub)
    if x.tail is not None:
        rv += x.tail + " "
    return rv



# Load the Treas Regs
# These XML files can be downloaded as a ZIP file from https://www.govinfo.gov/bulkdata/CFR/2020/title-26
print("Loading Treas Regs: ", end="")
tr_roots = []
for filename in os.listdir("CFR-title-26"):
    assert ".xml" in filename
    tree = ET.parse("CFR-title-26/" + filename)
    tr_roots.append((tree.getroot(), filename))
    print(".", end="")
print("")

# sort the filenames numerically
tr_roots.sort(key=lambda x: int(re.search("vol([1-9][0-9]?)[.]", x[1])[1]))

debug_call_info = []


# Returns a tuple of length of XML, length of Supp, number of recursive calls,
# number of dynamic programming entries, number of ellipses
def check_TreasReg(sec_num:str, supp_title_text:str, in_lines:list) -> (int, int, int, int):

    if not sec_num.startswith("1.263(a)-"):
        print("SECTION TOO TIME CONSUMING; SKIPPED")
        return (0,0,0,0,0,0)

    sec_num = utils.standardize(sec_num)
    print("-----------------------------------\nSection:", sec_num)
    tr_sec = None
    for r, filename in tr_roots:
        content = r.find("TITLE")
        for s in content.iter('SECTION'):
            if s.find("SECTNO") is not None:
                s_num = s.find("SECTNO").text
                if s_num[:2] != "§§": # skip the multi-section portions
                    if s_num[0] == "§":
                        s_num = s_num[1:].strip()
                    s_num = utils.standardize(s_num)
                    if s_num == sec_num:
                        assert tr_sec is None, "Should be only one match"
                        tr_sec = s

    if tr_sec is None:
        print("FAILED TO MATCH: ", sec_num, supp_title_text)
        return (0,0,0,0,0,0)

    # Check the title
    xml_heading_text = utils.standardize(tr_sec.find('SUBJECT').text).strip().strip(".")
    supp_title_text = utils.standardize(supp_title_text).strip().strip(".")
    if xml_heading_text != supp_title_text:
        print("FAILED TO MATCH HEADER ", sec_num)
        print("XML  :", xml_heading_text)
        print("Supp.:", supp_title_text)

    # gather the XML text
    xml_str = utils.standardize(get_TR_text_recursive(tr_sec))
    # print("Raw XML:", ET.tostring(irc_sec)) # useful for debug
    # print("XML text: ", re.sub("\n\\s*\n", "\n", xml_str)) # useful for debug
    xml_str = " ".join(xml_str.split()) # normalize whitespace

    # fix known typos in the official XML
    if "the unadjusted basis of the property in the hands of the son ins $90,000" in xml_str:
        xml_str = xml_str.replace("son ins $90,000", "son is $90,000")
    if "for sale to customers is includible in the empoyee" in xml_str:
        xml_str = xml_str.replace("in the empoyee", "in the employee")

    supp_str = utils.process_supp_lines(in_lines, sec_num)

    dual_indexes_tried = {}
    min_working_idx_ellipsis = {}
    result, num_recursive_calls = \
        utils.recursive_match(supp_str, 0, xml_str, 0, dual_indexes_tried, min_working_idx_ellipsis) # actual function call

    if not result:
        print("TREAS REG FAILURE", sec_num)
        utils.find_error(supp_str, xml_str)
        # print("XML string:", xml_str)
        # print("Raw XML:", ET.tostring(tr_sec)) # useful for debug
        # print("here")
    else:
        print("TREAS REG SUCCESS", sec_num)

    return len(xml_str), len(supp_str), \
           num_recursive_calls, len(dual_indexes_tried), \
           supp_str.count("…"), len(min_working_idx_ellipsis)


if __name__ == '__main__':
    sect_count = 0
    for idx, (r, filename) in enumerate(tr_roots):
        if "vol3." in filename: # debug
            print(idx, filename)
            content = r.find("TITLE")
            for s in content.iter('SECTION'):
                if s.find("SECTNO") is not None:
                    print(s.find("SECTNO").text, end=" ")
                    sect_count += 1
                if s.find("SUBJECT") is not None:
                    print(s.find("SUBJECT").text, end=" ")
                # print("Raw XML:", ET.tostring(s)) # useful for debug
                print(get_TR_text_recursive(s))
    print("Total sections =", sect_count)


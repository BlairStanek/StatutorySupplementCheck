# Created 15 Dec 2021 by Andrew Blair-Stanek largely from codecheck.py
# as part of breaking up the code into modules

import xml.etree.ElementTree as ET
import re

import utils

usc_ns_str = "http://xml.house.gov/schemas/uslm/1.0"

ns = {"usc" : usc_ns_str}


# Load the IRC itself
# usc26.xml was downloaded from https://uscode.house.gov/download/download.shtml
irc_tree = ET.parse("usc26.xml")
irc_root = irc_tree.getroot()

# Gets all non-header text from NON-repealed sections
def get_IRC_text_recursive(x:ET.Element, top_level = True) -> str:
    rv = ""
    if x.text is not None:
        rv += x.text + " "
    for sub in x:
        if "status" not in sub.attrib:
            if "sourceCredit" not in sub.tag and \
                    "notes" not in sub.tag and \
                    (not top_level or ("num" not in sub.tag and "heading" not in sub.tag)):
                rv += get_IRC_text_recursive(sub, False)
        else:
            # Count of statuses in all of IRC was the following: {'': 519201, 'repealed': 32}
            # Thus we are making the assumption asserted below
            assert sub.attrib["status"] == "repealed"
    if x.tail is not None:
        rv += x.tail + " "
    return rv




def check_IRC(sec_num:str, supp_title_text:str, in_lines:list):
    # if sec_num == "67": # for debug
    #     print("here")

    print("-----------------------------------\nSection:", sec_num)
    irc_sec = None
    for s in irc_root.iter('{' + usc_ns_str + '}section'):
        if "identifier" in s.attrib and \
                s.attrib["identifier"].lower() == "/us/usc/t26/s" + sec_num.lower():
            assert irc_sec is None, "Should be only one match"
            irc_sec = s
            assert s.find("usc:num", ns).attrib["value"].lower() == sec_num.lower()

    # Check the title
    xml_heading_text = utils.standardize(irc_sec.find('usc:heading', ns).text.strip()).strip(".")
    supp_title_text = supp_title_text.strip().strip(".")
    if xml_heading_text != supp_title_text:
        print("FAILED TO MATCH HEADER ", sec_num)
        print(xml_heading_text)
        print(supp_title_text)

    # gather the XML text
    xml_str = utils.standardize(get_IRC_text_recursive(irc_sec))
    # print("Raw XML:", ET.tostring(irc_sec)) # useful for debug
    # print("XML text: ", re.sub("\n\\s*\n", "\n", xml_str)) # useful for debug
    xml_str = " ".join(xml_str.split()) # normalize whitespace

    supp_str = utils.process_supp_lines(in_lines, sec_num)

    stored_results = {}
    result = utils.recursive_match(supp_str, 0, xml_str, 0, stored_results) # actual function call
    if not result:
        print("IRC FAILURE", sec_num)
        utils.find_error(supp_str, xml_str)
    else:
        print("IRC SUCCESS", sec_num)

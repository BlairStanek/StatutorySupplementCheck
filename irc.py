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

    if irc_sec is None:
        print("FAILED TO FIND SECTION:  ", sec_num, "   CANCELLING")

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
    xml_str = " ".join(xml_str.split()) # normalize whitespace

    supp_str = utils.process_supp_lines(in_lines, sec_num)

    dual_indexes_tried = {}
    fail_start_idx_ellipsis = {}
    result, num_recursive_calls = \
        utils.recursive_match(supp_str, 0, xml_str, 0, dual_indexes_tried, fail_start_idx_ellipsis) # actual function call
    if not result:
        print("IRC FAILURE", sec_num)
        utils.find_error(supp_str, xml_str)
        print("XML string:", xml_str)
    else:
        print("IRC SUCCESS", sec_num)

    return len(xml_str), len(supp_str), \
           num_recursive_calls, len(dual_indexes_tried), \
           supp_str.count("…"), len(fail_start_idx_ellipsis)


if __name__ == '__main__':
    print("Counting number of words and sections in IRC")
    section_count = 0 # only counts non-reserved sections
    sections_without_heading = 0
    sections_without_identifier = 0
    word_count = 0
    word_count_sections_without_heading = 0
    word_count_sections_without_identifier = 0
    last_named_section = "None"
    for s in irc_root.iter('{' + usc_ns_str + '}section'):
        section_count += 1
        section_text = utils.standardize(get_IRC_text_recursive(s))
        word_count += len(section_text.split())

        # The code below is used to print out a single section's text and stats.
        # If you paste the printed text into a Microsoft Word document, you see
        # that the word counts match.
        if "identifier" in s.attrib and \
                s.attrib["identifier"].lower() == "/us/usc/t26/s61":
            print("***********************************")
            print(section_text)
            print("Got total", len(section_text.split()))
            print("***********************************")

        if s.find('usc:heading', ns) is None:
            # There are some weird sections that seem to be statutes passed by Congress relating
            # to the IRC that appear in the XML as sections, but are not actual sections.  They
            # seem like they should have been put as notes at the end of sections, but were not.
            sections_without_heading += 1
            word_count_sections_without_heading += len(section_text.split())
            print("After", last_named_section, ", a no-heading section")
        else: # these are the normal sections
            title_text = utils.standardize(s.find('usc:heading', ns).text.strip()).strip(".")
            word_count += len(title_text.split())
            if "identifier" not in s.attrib:
                sections_without_identifier += 1
                word_count_sections_without_identifier += len(section_text.split()) + len(title_text.split())
                print("After", last_named_section, ", a no-identifier section")
            else:
                assert s.attrib["identifier"].startswith("/us/usc/t26/")
                last_named_section = s.attrib["identifier"][len("/us/usc/t26/"):]

    print("Total sections =", section_count)
    print("Total words =", word_count)
    print("Total sections without heading =", sections_without_heading)
    print("Total words in sections without heading =", word_count_sections_without_heading)
    print("Total sections without identifier =", sections_without_identifier)
    print("Total words in sections without identifier =", word_count_sections_without_identifier)

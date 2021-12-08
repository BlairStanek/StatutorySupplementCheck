# Created 7 Dec 2021 by Andrew to test whether the Code & Regs file matches up with
# the information in the official XML versions of the IRC and Treas Regs.

import xml.etree.ElementTree as ET
import re

usc_ns_str = "http://xml.house.gov/schemas/uslm/1.0"

ns = {"usc" : usc_ns_str}

hyphen_lookalikes_re = re.compile(r"[—–]") # em-dashes and en-dashes
def standardize(s:str) -> str:
    return " ".join(hyphen_lookalikes_re.sub("-", s).split())

# Gets all text from NON-repealed sections
def get_IRC_text_recursive(x:ET.Element) -> str:
    rv = ""
    if x.text is not None:
        rv += x.text + " "
    for sub in x:
        if "status" not in sub.attrib:
            if "sourceCredit" not in sub.tag and \
                    "notes" not in sub.tag:
                rv += get_IRC_text_recursive(sub)
        else:
            assert sub.attrib["status"] == "repealed"  # Count was the following: {'': 519201, 'repealed': 32}
    if x.tail is not None:
        rv += x.tail + " "
    return rv

# Load the IRC
tree = ET.parse("usc26.xml")
root = tree.getroot()


def check_IRC(sec_num:str, supp_title_text:str, in_lines:list):
    irc_sec = None

    for s in root.iter('{' + usc_ns_str + '}section'):
        if "identifier" in s.attrib and \
                s.attrib["identifier"].lower() == "/us/usc/t26/s" + sec_num.lower():
            irc_sec = s
            assert s.find("usc:num", ns).attrib["value"].lower() == sec_num.lower()

    xml_heading_text = standardize(irc_sec.find('usc:heading', ns).text.strip()).strip(".")
    supp_title_text = supp_title_text.strip().strip(".")

    if xml_heading_text != supp_title_text:
        print("FAILED TO MATCH!")
        print(xml_heading_text)
        print(supp_title_text)



# This manages the work of verifying that the title and text matches
def check_lines(in_lines):
    lines = []
    for l in in_lines:
        lines.append(standardize(l))

    sec_num, supp_title_text = lines[0][1:].split(maxsplit=1)
    if sec_num[-1] == ".":
        sec_num = sec_num[:-1] # remove the period if present

    if lines[0].startswith("§ 3.16 Standard Deduction") or \
            lines[0].startswith("§ 3.17."):
        print("Special treatment")
    elif "-" in sec_num:
        print("CFR")
    else:
        check_IRC(sec_num, supp_title_text, lines)



f = open("Code & Regs.txt", "r") # Load the file

current_in_lines = None # Don't store anything
for l in f.readlines():
    if l[0] == "§":  # Found a start of a section
        if current_in_lines is not None:
            check_lines(current_in_lines) # process prior section
        current_in_lines = [l] # reset and start gathering
    elif current_in_lines is not None:
        current_in_lines.append(l)
check_lines(current_in_lines) # handle the final section



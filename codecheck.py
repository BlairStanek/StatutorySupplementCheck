# Created 7 Dec 2021 by Andrew to test whether the Code & Regs file matches up with
# the information in the official XML versions of the IRC and Treas Regs.

import xml.etree.ElementTree as ET
import re

usc_ns_str = "http://xml.house.gov/schemas/uslm/1.0"

ns = {"usc" : usc_ns_str}

hyphen_lookalikes_re = re.compile(r"[—–]") # em-dashes and en-dashes
def standardize(s:str) -> str:
    return hyphen_lookalikes_re.sub("-", s)

statuses_count = {}

# Gets all text from NON-repealed sections
def get_text_recursive(x:ET.Element) -> str:
    rv = ""
    if x.text is not None:
        rv += x.text + " "
    for sub in x:
        if "status" not in sub.attrib:
            if "sourceCredit" not in sub.tag and \
                    "notes" not in sub.tag:
                rv += get_text_recursive(sub)
        else:
            assert sub.attrib["status"] == "repealed"  # Count was the following: {'': 519201, 'repealed': 32}
    if x.tail is not None:
        rv += x.tail + " "
    return rv

# Load the IRC
tree = ET.parse("usc26.xml")
root = tree.getroot()


# This manages the work of verifying that the title and text matches
def check_lines(in_lines):
    lines = []
    for l in in_lines:
        lines.append(standardize(l))

    sec_num, title_text = l[1:].split(maxsplit=1)
    if sec_num[-1] == ".":
        sec_num = sec_num[:-1] # remove the period if present

    if l.startswith("§ 3.16 Standard Deduction") or l.startswith("§ 3.17."):
        print("Special treatment")
    elif "-" in sec_num:
        print("CFR")
    else:
        irc_sec = None
        for s in root.iter('{' + usc_ns_str + '}section'):
            if "identifier" in s.attrib and \
                    s.attrib["identifier"].lower() == "/us/usc/t26/s" + sec_num.lower():
                irc_sec = s
                assert s.find("usc:num", ns).attrib["value"].lower() == sec_num.lower()
            # for subval in s:
            #     if subval.tag == '{http://xml.house.gov/schemas/uslm/1.0}num' and \
            #         subval.attrib["value"] == sec_num:
            #         # if sec_num == s.find('{http://xml.house.gov/schemas/uslm/1.0}num').attrib["value"]:
            #         irc_sec = s
            #         break
        heading_text = standardize(irc_sec.find('usc:heading', ns).text.strip())
        title_text = title_text.strip()
        if heading_text[-1] == ".":
            heading_text = heading_text[:-1]
        if title_text[-1] == ".":
            title_text = title_text[:-1]

        if heading_text != title_text:
            print("FAILED TO MATCH!")
            print(heading_text)
            print(title_text)

        # section_text = get_text_recursive(irc_sec)
        # section_text = re.sub("\n\\s*\n", "\n", section_text)  # remove unnecessary newlines
        #
        # print(section_text)




# Load the file and identify the sections
f = open("Code & Regs.txt", "r")

current_in_lines = []

for l in f.readlines():
    # Found a start of a section
    if l[0] == "§":
        check_lines(current_in_lines) # process prior section
        current_in_lines = [l] # reset




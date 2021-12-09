# Created 7 Dec 2021 by Andrew Blair-Stanek to test whether the hand-curated
# Code & Regs file that I made for my class matches up with
# the information in the official XML versions of the IRC and Treas Regs.

import xml.etree.ElementTree as ET
import re

usc_ns_str = "http://xml.house.gov/schemas/uslm/1.0"

ns = {"usc" : usc_ns_str}

hyphen_lookalikes_re = re.compile(r"[—–]") # em-dashes and en-dashes
def standardize(s:str) -> str:
    return " ".join(hyphen_lookalikes_re.sub("-", s).split())

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

# Load the IRC
tree = ET.parse("usc26.xml")
root = tree.getroot()


def recursive_IRC_match(supp_str:list, supp_idx_start:int,
                        xml_str:list, xml_idx_start:int) -> bool:
    if supp_idx_start >= len(supp_str) or xml_idx_start >= len(xml_str):
        return False

    supp_idx = supp_idx_start
    xml_idx = xml_idx_start

    while supp_idx < len(supp_str) and \
        xml_idx < len(xml_str) and \
        supp_str[supp_idx] == xml_str[xml_idx]:
        supp_idx += 1
        xml_idx += 1
    if supp_idx == len(supp_str) and xml_idx == len(xml_str):
        return True # reached end with matching
    if supp_idx == len(supp_str)-1 and supp_str[supp_idx] in ["....", "…", "..."]:
        return True # reached end, with ellipses in supp taking us to the end
    if supp_idx >= len(supp_str) or xml_idx >= len(xml_str):
        return False # we've gone beyond the end of one but not the other
    if supp_str[supp_idx] in ["…", "...", "....", "…."]:
        for i in range(xml_idx+1, len(xml_str)):
            if supp_str[supp_idx+1] == xml_str[i]: # try the next match
                success = recursive_IRC_match(supp_str, supp_idx+1, xml_str, i)
                if success:
                    return True
    if supp_str[supp_idx:supp_idx+2] == ". ": # handle the mysterious missing periods in XML version
        success = recursive_IRC_match(supp_str, supp_idx+1, xml_str, xml_idx)
        if success:
            return success
    if supp_str[supp_idx] == "[" and supp_str[supp_idx+1:supp_idx+2] != "]": # handle comments
        while True:
            supp_idx +=1
            if supp_idx >= len(supp_str):
                return False
            if supp_str[supp_idx] == "]":
                supp_idx +=1 # advance to beyond the first comment
                break
        if supp_idx < len(supp_str):
            success = recursive_IRC_match(supp_str, supp_idx, xml_str, xml_idx)
            if success:
                return success
    # if supp_idx < len(supp_str) and \
    #         supp_str[supp_idx] == " ": # advance over whitespace
    #     success = recursive_IRC_match(supp_str, supp_idx+1, xml_str, xml_idx)
    #     if success:
    #         return success
    # if xml_idx < len(xml_str) and \
    #         xml_str[xml_idx] == " ": # advance over whitespace
    #     success = recursive_IRC_match(supp_str, supp_idx, xml_str, xml_idx+1)
    #     if success:
    #         return success

    if supp_idx > supp_idx_start+10:
        print("Problems started at: ")
        print("Supp: ", supp_str[max(0, supp_idx-5): supp_idx], " +++ ",
             supp_str[supp_idx:min(len(supp_str), supp_idx+40)])
        print("XML : ", xml_str[max(0, xml_idx-5): xml_idx], " +++ ",
              xml_str[xml_idx:min(len(xml_str), xml_idx+40)])

    return False # we couldn't find a good match


def check_IRC(sec_num:str, supp_title_text:str, in_lines:list):
    print("Section:", sec_num)
    irc_sec = None
    for s in root.iter('{' + usc_ns_str + '}section'):
        if "identifier" in s.attrib and \
                s.attrib["identifier"].lower() == "/us/usc/t26/s" + sec_num.lower():
            assert irc_sec is None, "Should be only one match"
            irc_sec = s
            assert s.find("usc:num", ns).attrib["value"].lower() == sec_num.lower()

    # Check the title
    xml_heading_text = standardize(irc_sec.find('usc:heading', ns).text.strip()).strip(".")
    supp_title_text = supp_title_text.strip().strip(".")
    if xml_heading_text != supp_title_text:
        print("FAILED TO MATCH HEADER ", sec_num)
        print(xml_heading_text)
        print(supp_title_text)

    # Check the text
    xml_str = standardize(get_IRC_text_recursive(irc_sec))
    # print("Raw XML:", ET.tostring(irc_sec))
    # print("XML text: ", re.sub("\n\\s*\n", "\n", xml_str))
    xml_str = " ".join(xml_str.split()) # normalize whitespace
    supp_str = ""
    for i in range(1, len(in_lines)):
        supp_str += in_lines[i] + " "
    supp_str = " ".join(supp_str.split()) # normalize whitespace

    result = recursive_IRC_match(supp_str, 0, xml_str, 0) # actual function call
    if not result:
        print("FAILURE")
    else:
        print("SUCCESS")



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



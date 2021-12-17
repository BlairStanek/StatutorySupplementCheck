# Created 7 Dec 2021 by Andrew Blair-Stanek to test whether the hand-curated
# Code & Regs file that I made for my class matches up with
# the information in the official XML versions of the IRC and Treas Regs.

import xml.etree.ElementTree as ET
import re
import irc, treasregs, utils

special_treatment_starts = ["Chapter",
                            "State and Local Bond Interest",
                            "Revenue Procedure 2021-45",
                            "§ 3.16 Standard Deduction",
                            "§ 3.17.",
                            "Prop. Reg."]  # alas, proposed regs aren't in the CFR


# This manages the work of verifying that the title and text matches
def check_lines(in_lines:list, perf_data:list):
    lines = []
    for l in in_lines:
        lines.append(utils.standardize(l))

    sec_num, supp_title_text = lines[0][1:].split(maxsplit=1)
    if sec_num[-1] == ".":
        sec_num = sec_num[:-1] # remove the period if present

    if True in [lines[0].startswith(s) for s in special_treatment_starts]:
        print("Special treatment")
    elif "-" in sec_num:
        perf_tuple = treasregs.check_TreasReg(sec_num, supp_title_text, lines)
        perf_data.append((sec_num, perf_tuple))
    # else:
    #     perf_tuple = irc.check_IRC(sec_num, supp_title_text, lines)
    #     perf_data.append((sec_num, perf_tuple))


f = open("Code & Regs.txt", "r") # Load the file

perf_data = []
current_in_lines = None # Don't store anything until we find a section
for idx_l, l in enumerate(f.readlines()):

    if l[0] == "§" or True in [l.startswith(s) for s in special_treatment_starts]:  # Found a start of a section
        print("----- At Line", idx_l)
        if current_in_lines is not None:
            check_lines(current_in_lines, perf_data) # process prior section
        current_in_lines = [l] # reset and start gathering
    elif current_in_lines is not None:
        current_in_lines.append(l)
check_lines(current_in_lines, perf_data) # handle the final section

for sec_num, perf_tuple in perf_data:
    print("{:10s} {:7.3f} {:6d} {:6d} {:6d} {:6d} {:6d}".format(sec_num,
                                                                (perf_tuple[3]/float(perf_tuple[0]+0.0001)), \
                                                            perf_tuple[0], \
                                                           perf_tuple[1], perf_tuple[2],
                                                           perf_tuple[3], perf_tuple[4]))
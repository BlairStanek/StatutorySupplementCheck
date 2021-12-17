# Created 15 Dec 2021 by Andrew Blair-Stanek to handle utility functions used
# throughout the IRC and CFR verification
import re
import string

hyphen_lookalikes_re = re.compile(r"[—–]") # em-dashes and en-dashes
def standardize(s:str) -> str:
    rv = hyphen_lookalikes_re.sub("-", s).replace("--", "-")
    rv = rv.replace("“", "\"").replace("”", "\"").replace("’", "'").replace("‘", "'")
    return " ".join(rv.split())

def recursive_match(supp_str:str, supp_idx_start:int,
                        xml_str:str, xml_idx_start:int, 
                        dual_indexes_tried:dict, fail_start_idx_ellipsis:dict) -> (bool, int):
    num_recursive_calls = 1 # will be returned; used for performance and debug

    supp_idx = supp_idx_start
    xml_idx = xml_idx_start

    while True:  # main loop to advance as far as possible
        # if supp_idx > 940:
        #     print("", end="")
        # if supp_str[supp_idx:].startswith("for any taxable year beginning after"):
        #     assert True

        if supp_idx == len(supp_str) and xml_idx == len(xml_str):
            return True, num_recursive_calls # then we have matched
        elif supp_idx == len(supp_str) or xml_idx == len(xml_str):
            return False, num_recursive_calls # then only one matched
        if supp_str[supp_idx] == xml_str[xml_idx]: # exact match => advance both
            supp_idx += 1
            xml_idx += 1
        elif supp_str[supp_idx:supp_idx+2] == ". " and xml_str[xml_idx:xml_idx+1] == " ":
            supp_idx += 1 # handle the mysterious missing periods in XML version
        # elif supp_str[supp_idx:supp_idx+2] == ", " and xml_str[xml_idx:xml_idx+3] == " , ":
        #     xml_idx += 1 # handle the mysterious extra space before commas in the XML
        elif supp_str[supp_idx:supp_idx+2] == " …":
            supp_idx += 1
        elif supp_str[supp_idx:supp_idx+1].isspace() and xml_str[xml_idx:xml_idx+1] in ["-", "("]: # advance over extra spaces added
            supp_idx += 1
        elif xml_str[xml_idx:xml_idx+1].isspace() and supp_str[supp_idx:supp_idx+1] in string.punctuation : # advance over extra spaces added
            xml_idx += 1
        else:
            break # then we need to consider the next possibilities

    # skip over ellipses
    if supp_str[supp_idx:supp_idx+1] == "…":
        supp_idx += 1 # skip over ellipsis
        if supp_str[supp_idx:supp_idx+1].isspace():
            supp_idx += 1 # skip over spaces after ellipses

        i_start = xml_idx+1
        i_end = len(xml_str)+1 # we potentially consider the end of string for a match, hence the +1
        if supp_idx in fail_start_idx_ellipsis:
            # then we have previously tried matching this ellipses up with at
            # least some part of the remaining string, so don't try that
            i_end = fail_start_idx_ellipsis[supp_idx]

        for i in range(i_start, i_end):
            relevant_tuple = (supp_idx, i)
            if relevant_tuple not in dual_indexes_tried:
                success, num_subcalls = \
                    recursive_match(supp_str, supp_idx, xml_str, i, dual_indexes_tried, fail_start_idx_ellipsis)
                num_recursive_calls += num_subcalls

                dual_indexes_tried[relevant_tuple] = success # dynamic programming to avoid waste
                if len(dual_indexes_tried) % 30000 == 0 and len(dual_indexes_tried) > 0:
                    print("  call", len(dual_indexes_tried))
            assert relevant_tuple in dual_indexes_tried, "Should have been handled"
            if dual_indexes_tried[relevant_tuple] == True:
                return True, num_recursive_calls
        # since we are here, all attempts failed, so store if relevant
        # (this is dynamic programming)
        fail_start_idx_ellipsis[supp_idx] = i_start

    return False, num_recursive_calls # we couldn't find a good match



def find_error(supp_str:str, xml_str:str):
    idx_known_bad = len(supp_str) # we know full is not a good match
    idx_known_good = 0 # we know zero will be a good match
    while idx_known_good < idx_known_bad-1:
        # print("Searching for Error,  idx_known_good=", idx_known_good, " idx_known_bad=",idx_known_bad)
        idx_to_try = int((idx_known_good+idx_known_bad)/2) # basically binary search
        dual_indexes_tried = {}
        fail_start_idx_ellipsis = {}
        str_to_try = supp_str[:idx_to_try]+"…"
        # print("Trying:", str_to_try)
        success, _ = recursive_match(str_to_try, 0, xml_str, 0, \
                                  dual_indexes_tried, fail_start_idx_ellipsis)
        # print("success =", success)
        if success:
            idx_known_good = idx_to_try
        else:
            idx_known_bad = idx_to_try
    assert idx_known_good == idx_known_bad-1
    print("PROBLEM at ", supp_str[max(0,idx_known_good-40):idx_known_good], "<-->", supp_str[idx_known_bad-1:idx_known_bad+25])
    # print(" FULL CONTEXT ", supp_str[idx_known_good-400:idx_known_good+1], "<-->", supp_str[idx_known_bad:idx_known_bad+400])


def process_supp_lines(in_lines:list, sec_num:str) -> str:
    # gather the supplement text
    supp_str = ""
    for i in range(1, len(in_lines)):
        supp_str += in_lines[i] + " "
    supp_str = supp_str.replace("...", "…") # standardize ellipses
    supp_str = supp_str.replace("[]", "…") # standardize [] into an ellipse (equivalent!)
    supp_str = re.sub("(\s?\[)([^\]]+)(\])", "", supp_str) # remove comments
    supp_str = " ".join(supp_str.split()) # normalize whitespace
    if sec_num == "1231" and supp_str[-1:] == "7": # handles the weird extra character
        supp_str = supp_str[:-1].strip()
    return supp_str
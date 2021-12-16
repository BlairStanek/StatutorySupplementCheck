# Created 15 Dec 2021 by Andrew Blair-Stanek to handle utility functions used
# throughout the IRC and CFR verification
import re

hyphen_lookalikes_re = re.compile(r"[—–]") # em-dashes and en-dashes
def standardize(s:str) -> str:
    rv = hyphen_lookalikes_re.sub("-", s).replace("--", "-")
    rv = rv.replace("“", "\"").replace("”", "\"").replace("’", "'").replace("‘", "'")
    return " ".join(rv.split())



def recursive_match(supp_str:str, supp_idx_start:int,
                        xml_str:str, xml_idx_start:int, stored_results:dict) -> bool:

    supp_idx = supp_idx_start
    xml_idx = xml_idx_start

    while True:  # main loop to advance as far as possible
        # if supp_idx > 940:
        #     print("", end="")
        # if supp_str[supp_idx:].startswith("for any taxable year beginning after"):
        #     assert True

        if supp_idx == len(supp_str) and xml_idx == len(xml_str):
            return True # then we have matched
        elif supp_idx == len(supp_str) or xml_idx == len(xml_str):
            return False # then only one matched
        if supp_str[supp_idx] == xml_str[xml_idx]: # exact match => advance both
            supp_idx += 1
            xml_idx += 1
        elif supp_str[supp_idx:supp_idx+2] == ". " and xml_str[xml_idx:xml_idx+1] == " ":
            supp_idx += 1 # handle the mysterious missing periods in XML version
        # elif supp_str[supp_idx:supp_idx+2] == ", " and xml_str[xml_idx:xml_idx+3] == " , ":
        #     xml_idx += 1 # handle the mysterious extra space before commas in the XML
        elif supp_str[supp_idx:supp_idx+1].isspace(): # advance over extra spaces added
            supp_idx += 1
        elif xml_str[xml_idx:xml_idx+1].isspace(): # advance over extra spaces added
            xml_idx += 1
        # elif supp_str[supp_idx] == "[" and supp_str[supp_idx+1:supp_idx+2] != "]":
        #     # handle comments by advancing until the end of the comment
        #     idx_supp_open_bracket = supp_idx
        #     supp_idx += 2 # advance two, since we
        #     while supp_idx < len(supp_str) and supp_str[supp_idx] != "]":
        #         supp_idx += 1
        #     if supp_idx == len(supp_str):
        #         print("Failure due to mismatched comments, starting at", supp_str[idx_supp_open_bracket-5:idx_supp_open_bracket+5])
        #         return False
        #     assert supp_str[supp_idx] == "]"
        #     supp_idx += 1 # skip over the ]
        #     if supp_idx < len(supp_str) and supp_str[supp_idx].isspace(): # skip over any subsequent space
        #         supp_idx += 1
        else:
            break # then we need to consider the next possibilities

    # skip over ellipses
    if supp_str[supp_idx:supp_idx+1] == "…":
        supp_idx += 1 # skip over ellipsis
        if supp_str[supp_idx:supp_idx+1].isspace():
            supp_idx += 1 # skip over spaces after ellipses
        for i in range(xml_idx+2, len(xml_str)+1): # we consider the end of string, hence the +1
            relevant_tuple = (supp_idx, i)
            if relevant_tuple not in stored_results:
                success = recursive_match(supp_str, supp_idx, xml_str, i, stored_results)
                stored_results[relevant_tuple] = success
            assert relevant_tuple in stored_results, "Should have been handled"
            if stored_results[relevant_tuple] == True:
                return True

    return False # we couldn't find a good match



def find_error(supp_str:str, xml_str:str):
    idx_known_bad = len(supp_str) # we know full is not a good match
    idx_known_good = 0 # we know zero will be a good match
    while idx_known_good < idx_known_bad-1:
        print("Searching for Error,  idx_known_good=", idx_known_good, " idx_known_bad=",idx_known_bad)
        idx_to_try = int((idx_known_good+idx_known_bad)/2) # basically binary search
        stored_results = {}
        success = recursive_match(supp_str[:idx_to_try]+"…", 0, xml_str, 0, stored_results)
        if success:
            idx_known_good = idx_to_try
        else:
            idx_known_bad = idx_to_try
    assert idx_known_good == idx_known_bad-1
    print("PROBLEM at ", supp_str[idx_known_good-25:idx_known_good+1], "<-->", supp_str[idx_known_bad:idx_known_bad+25])
    print(" FULL CONTEXT ", supp_str[idx_known_good-400:idx_known_good+1], "<-->", supp_str[idx_known_bad:idx_known_bad+400])


def process_supp_lines(in_lines:list, sec_num:str) -> str:
    # gather the supplement text
    supp_str = ""
    for i in range(1, len(in_lines)):
        supp_str += in_lines[i] + " "
    supp_str = supp_str.replace("...", "…") # standardize ellipses
    supp_str = supp_str.replace("[]", "…") # standardize [] into an ellipse (equivalent!)
    supp_str = re.sub("(\[)([^\]]+)(\])", "", supp_str) # remove comments
    supp_str = " ".join(supp_str.split()) # normalize whitespace
    if sec_num == "1231" and supp_str[-1:] == "7": # handles the weird extra character
        supp_str = supp_str[:-1].strip()
    return supp_str
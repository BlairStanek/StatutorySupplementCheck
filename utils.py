# Created 15 Dec 2021 by Andrew Blair-Stanek to handle utility functions used
# throughout the IRC and CFR verification
import re

hyphen_lookalikes_re = re.compile(r"[—–]") # em-dashes and en-dashes
def standardize(s:str) -> str:
    return " ".join(hyphen_lookalikes_re.sub("-", s).replace("--", "-").replace("“", "\"").replace("”", "\"").split())

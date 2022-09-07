# StatutorySupplementCheck
Checks whether a hand-curated tax-law class statutory supplement matches the latest official IRC and Treas Reg.  
To run, here are the steps:
1) Save your statutory supplement as "Code & Regs.txt" and put it in the current directory
2) Download the latest XML version of the IRC from https://uscode.house.gov/download/download.shtml and put it at usc26.xml in the current directory
3) Download the latest XML version of the Treasury regulations from https://www.govinfo.gov/bulkdata/CFR/2020/title-26 and put all the XML files into the directory CFR-title-26 inside the current directory
4) Run python codecheck.py

It checks for up-to-dateness and correctness.  It handles ellipses.  Anything between two square brackets is ignored, as that is the format for comments.  There are some handling of weird error cases from the XML and my own statutory supplement.  You can see an example statutory supplement, which is in the repo as Code & Regs.docx (but remember that you need to save as Code & Regs.txt).  

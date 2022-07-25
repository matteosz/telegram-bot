import string, re
from fuzzywuzzy import fuzz

def tokenize(s):
    # Remove punctuation and return the list of words from a string
    for c in string.punctuation:
        s = s.replace(c, ' ')
    t = s.replace('nbsp',' ').split(' ')
    try:
        t.remove('')
    except: pass
    return t

def compare(description,search):
    # Process the adv string removing useless info, search string is processed at the source
    keywords_adv = tokenize(description)
    match = 0
    for w in search:
        for k in keywords_adv:
            score = fuzz.WRatio(w,k) 
            if score >= 95: # 95% accuracy to match
                match += 1
                break 
    return match

def extract_subitem(pattern,text):
    # Extract the text contained in the pattern
    try:
        out = re.search(pattern, text).group(1)
    except:
        out = None
    return out
    
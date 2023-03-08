# GATE
GATE: A Challenge Set for Gender-Ambiguous Translation Examples

This repository contains the GATE corpus as well as code for evaluation with GATE (GateEval.py). 
You can find our paper detailing the development of and uses for GATE at https://arxiv.org/abs/2303.03975

## GATE Corpus

GATE contains thousands of sentence tuples, each consisting of a single English sentence, along with two or more translations into Spanish, French or Italian. Each sentence tuple contains at least one AGME (Arbitrarily Gender-Marked Entity), which is an animate noun that is unmarked for gender in the English source but marked for gender in the target language. For tuples containing three or fewer AGMEs, we provide translations for each possible combination of genders over those AGMEs (typically 2, 4, or 8 translations for 1, 2 or 3 AGMEs respectively). 

The corpus for each language can be found under .../data with each language's two letter acronym -- ES for Spanish, FR for French and IT for Italian.
Each language directory contains a tsv for 2, 4, or 8 variants (depending on AGME count), as well as compact and readable json files containing all sentence tuples.
You will also find an "XX_report.txt" file giving counts for noun vocab items and category labels (see below).

The French directory additionally contains a copy of the tsv files where the French text fields use Right Single Quotation Mark (U+2019) in place of ascii apostrophes as this is the preferred character to use in contractions under many French style guides. Versions of the French json files with Right Single Quotation Mark are not included.

Half of the sentences in each tsv file, selected at random, are marked as "dev" and the other half as "test". 
We encourage users to use the "dev" subset for in-depth debugging, and to reserve "test" primarily as a held-out evaluation set.

### Key words

Each tuple is additionally accompanied by a set of "key words" indicating nouns representing AGMEs and in some cases other portions of the sentence that mark gender.
Typically this will be the head noun of a noun phrase representing an AGME, and possibly some additional supporting words. 

You will find three "key words" columns in each tsv: kw_s (source key words), kw_f (feminine key words) and kw_m (masculine key words). Some special cases:
- If supporting words aside from the head noun are included, the head noun is enclosed in square brackets.
  - e.g. you may see kw_s = "police [officer]",  kw_m=kw_f = "policía" 
- In cases where an AGME is referred to by multiple coreferent mentions, they will be joined together by "=".
- For sentences with multiple AGMEs, key word fields will use "," as an AGME delimiter.
- AGMEs which have no overt mention and only a dropped subject pronoun will typically be indicated with a nominative case pronoun enclosed in parentheses, e.g. for the sentence tuple "I'm tired." -> "Estoy cansada/cansado", the kw_f and kw_m would contain "(yo)"

### Category labels

Each sentence tuple is also accompanied by a set of category labels that descibe several features about that tuple. 
For example, some labels indicate what grammatical role an AGME plays (SUBJ for subject, DOBJ for direct object, ...), or an animate noun type (PROF for profession,
FAM for "family or relationship", ...) and so on. These category labels can help to identify strong and weak points in a gender rewrite system, 
and GateEval.py will give a breakdown of statistics per category label.

Refer to Appendix A of our paper for a comprehensive list of category labels and additional discussion.

### Limitations

Upon analyzing this version of the data, we find some inconsistencies and omissions.

The above guidelines for key words were followed somewhat loosely and with a fair amount of variation between languages. 
While they are useful guides for a human reader, they may therefore be difficult to make use of programmatically.

A few of the category labels were not annotated consistently or correctly.
Of particular note: 
- INDF (indefinite -- some speakers may find a masculine generic natural) was only annotated for Italian.
- GLNK (gender link -- two distinct groups would likely be treated as a single group for gender determination), was annotated only for French and not always accurately; 
- APPS (post-positive adjective construction) -- Placement of adjectives after nouns in romance languages is typical, so this doesn't actually capture special structures as in English. inconsistently annotated.

## Evaluation with GateEval.py

GateEval.py is intended to aid in evaluation with GATE. Typical use entails sentence-level comparison of a set of rewritten target translations with references
found in one of the two-variant tsv files in GATE. Only exact sentence matches are considered correct. Lines may be left blank to indicate a null output -- 
these count as recall errors but not precision errors.

Rewriter output should be placed into a utf-8 text file with one sentence per line and no header. 
From the root directory of this enlistment it could be invoked on female-to-male rewriter output (rewriter_hyps_f2m.txt) as follows:

py GateEval.py --reference_file_name data/ES/ES_2_variants.tsv --predicted_file_name rewriter_hyps_f2m.txt --gender masculine

This would produce (to stdout) precision, recall and F0.5 for the entire dataset, as well as for the subset of sentences associated with each category label.

--max_words and --min_words can also be added to restrict to only the portion of the dataset in that range of lengths (calculated by whitespace splitting the source sentence).
Normally sentences outside the length range will not be included in calculations at all. However, if the --full_set_recall option is also added, those sentences will instead
be treated as null outputs, and therefore recall errors.

GateEval.py supports only evaluation over single-AGME (i.e. two-variant) tuples.

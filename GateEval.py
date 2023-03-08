import csv
import argparse
from enum import IntEnum

# Script to compute precision and recall reference data of GATE Paper
# It currently has two features:
# 1. Compute Precision and Recall: 
#   python .\GateEval.py --reference_file_name .\French_reviewed.txt --predicted_file_name .\French_translated.generated.txt --gender feminine 
# 2. Extract a gendered predicted content from reference data:
#   python .\GateEval.py --reference_file_name .\French_reviewed.txt --predicted_file_name .\French_translated.generated.feminine.txt --gender feminine --extract_column
#   extract a column from reference data to --predicted_file_name

class MatchResult(IntEnum):
    Match = 0
    Mismatch = 1
    Empty = 2

# Parse reference file
def parse_reference_doc(reference_file_name):
    """
    Parse all data from reference_file_name into a list of dicts (one per line) mapping column name to value
    """
    try:
        reference_data = []
        with open(reference_file_name, 'r',  encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            headers = next(reader)
            header_size = len(headers)
            skipped_row_count = 0
            for row in reader:
                if (len(row) == header_size):
                    record = {}
                    for i in range(len(headers)):
                        record[headers[i]] = row[i]
                    reference_data.append(record)
                else:
                    # todo remove this after we fix spanish data
                    skipped_row_count += 1
                    print(f'Incompatible data Skipping row: {reader.line_num}.')
        print(f'Skipped {skipped_row_count} rows out of {reader.line_num} due to unexpected formatting')
        return reference_data
    except FileNotFoundError:
        print(f"The file {reference_file_name} could not be found.")
        raise

def parse_predicted_doc(predictions_file_name):
    try:
        predicted_data = []
        with open(predictions_file_name, 'r',  encoding='utf-8') as f:
            predicted_data = f.read().splitlines()
            return predicted_data
    except FileNotFoundError:
        print(f"The file {predictions_file_name} could not be found.")
        raise

def generate_predicted_doc(reference_data, gender, predicted_file_name):
    # open file in write mode
    with open(predicted_file_name, 'w',  encoding='utf-8') as fw:
        for  i in range(len(reference_data)):
            # write each item on a new line
            fw.write("%s\n" % reference_data[i][gender])


def compute_stats(match_array, filter=None, recall_denom=None):
    """Calculate precision, recall and F0.5 for a subset of the data set. 
    filter is an array of booleans, if it is not None calculate only on the portion where filter is True
    if recall_denom is not None, calculate recall against that amount (generally before length filter has been added to filter)
    """
    match_type_counts = [0, 0, 0]
    for i in range(len(match_array)):
        if filter is None or filter[i]:
            match_type_counts[match_array[i]] += 1

    prec_denom = (match_type_counts[MatchResult.Match] + match_type_counts[MatchResult.Mismatch])
    precision = match_type_counts[MatchResult.Match] / prec_denom if prec_denom > 0 else 0

    count = sum(match_type_counts)
    if recall_denom is None:
        recall_denom = count
    recall = match_type_counts[MatchResult.Match] / recall_denom if recall_denom > 0 else 0

    f0_5 = calc_f_beta(precision, recall, 0.5)
    
    return precision, recall, f0_5, count

def calc_f_beta(p, r, beta):
    b_2 = beta * beta
    denom = (b_2 * p) + r
    if denom == 0:
        return 0

    return (1 + b_2) * (p * r) / denom

def get_sent_match(pred, ref):
    if len(pred.strip()) == 0:
        return MatchResult.Empty
    elif pred.strip() == ref.strip():
        return MatchResult.Match
    else:
        return MatchResult.Mismatch

def get_category_filters(reference_data):
    """
    Build a dict mapping each category label to the set of sentences that have that label 
    """
    sent_labels = []
    all_cats = set()
    for row in reference_data:
        cats = row['labels'].strip().split(';')
        sent_labels.append(cats)
        all_cats.update(cats)

    cat_map = {x: [False for y in reference_data] for x in all_cats}
    for i in range(len(sent_labels)):
        for lbl in sent_labels[i]:
            cat_map[lbl][i] = True

    return cat_map

def get_match_array(predicted_data, reference_data, gender):
    """
    match each sentence against its reference and generate an array of which ones match or were left blank (passed)
    """
    return [get_sent_match(predicted_data[i], reference_data[i][gender]) for i in range(len(predicted_data))]

def get_length_filter(reference_data, max_words, min_words):
    """
    generate an array of bools for sentences whose lenghts fall between the min and max word lenghts (if present)
    """
    if max_words is None:
        max_words 

    filter = []
    for row in reference_data:
        num_words = len(row['source'].strip().split())
        filter.append((max_words is None or num_words <= max_words) and (min_words is None or num_words >= min_words))
    return filter

def intersect_filters(*filters):
    """
    combine multiple boolean filter arrays by intersecting. Will be true only if all input sets are true for that index.
    """
    if len(filters) == 0:
        return []

    result = []
    for i in range(len(filters[0])):
        cur = True
        for j in range(len(filters)):
            if not filters[j][i]:
                cur = False
                break
        result.append(cur)
    return result

parser = argparse.ArgumentParser()
parser.add_argument("--reference_file_name", help="Path to the reference label file")
parser.add_argument("--predicted_file_name", help="Path to the predicted file")
parser.add_argument("--gender", default="feminine", choices=["masculine", "feminine"], help="Predicted gender")
parser.add_argument("--extract_column", default=False, action=argparse.BooleanOptionalAction, help="extract --gender column from --reference_file_name and write it to --predicted_file_name")
parser.add_argument("--max_words", type=int, help="Ignore sentences longer than the specified length")
parser.add_argument("--min_words", type=int, help="Ignore sentences shorter than the specified length")
parser.add_argument("--full_set_recall", type=bool, default=False, action=argparse.BooleanOptionalAction, help="Count sentences longer and shorter than limits in the denominator for recall")
args = parser.parse_args()

reference_file_name = args.reference_file_name
predicted_file_name = args.predicted_file_name
predicted_content_gender =  "f" if args.gender == "feminine" else "m"
should_generate_predicted_file = args.extract_column
max_words = args.max_words
min_words = args.min_words
full_set_recall = args.full_set_recall

try:
    # parse reference data
    reference_data = parse_reference_doc(reference_file_name)

    if should_generate_predicted_file:
        #generate predicted file of specified gender
        print(f"Extracting column to 'predicted_file': {predicted_file_name} with Gender: {args.gender}.")
        generate_predicted_doc(reference_data, predicted_content_gender, predicted_file_name)
        print(f"Completed generating predicted_file: {predicted_file_name}, entries: {len(reference_data)} with Gender: {args.gender}.")

    else:
        # parse predicted data
        predicted_data = parse_predicted_doc(predicted_file_name)
        match_array = get_match_array(predicted_data, reference_data, predicted_content_gender)
        length_filter = get_length_filter(reference_data, max_words, min_words)

        print(f"reference_file: {reference_file_name}")
        print(f"predicted_file: {predicted_file_name}")
        print(f"Gender: {args.gender}")
        print(f"max_words: {max_words}")

        # compute precision and recall
        recall_denom = len(match_array) if full_set_recall else None
        precision, recall, f0_5, count = compute_stats(match_array, length_filter, recall_denom)
        print(f"Overall {count:4} -- Precision: {precision:.3f}, Recall: {recall:.3f}, f0.5: {f0_5:.3f}")
        
        cat_filters = get_category_filters(reference_data)
        for (cat, filt) in cat_filters.items():
            recall_denom = sum(1 for x in filt if x) if full_set_recall else None
            filter = intersect_filters(filt, length_filter) if length_filter is not None else filt

            cat_p, cat_r, cat_f, cat_count = compute_stats(match_array, filter, recall_denom)
            print(f"{cat}\t{cat_count:4} -- Precision: {cat_p:.3f}, Recall: {cat_r:.3f}, f0.5: {cat_f:.3f}")

except Exception as e:
    print(f"An error occurred: {e}")
    raise
    
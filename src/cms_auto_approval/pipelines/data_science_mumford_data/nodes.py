import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import re
from sklearn.metrics import classification_report
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import log_loss
from sklearn.metrics import precision_score
import logging
log = logging.getLogger(__name__)

def jaccard_similarity(row, col_a: str, col_b:str) -> float:

    MAXIMUM_WORDS = 100

    try:
        text_a = row[col_a].split()[:MAXIMUM_WORDS]
        text_b = row[col_b].split()[:MAXIMUM_WORDS]
        intersection = set(text_a).intersection(set(text_b))
        union = set(text_a).union(set(text_b))
        return round(len(intersection)/len(union), 2)
    except:
        return 0

def is_string_like_product_code(input_str: str) -> bool: 
    
    # intializing flag variable 
    flag_l = False
    flag_n = False
      
    # checking for letter and numbers in given string 
    for i in input_str: 
        
        # if string has letter 
        if i.isalpha(): 
            flag_l = True
  
        # if string has number 
        if i.isdigit(): 
            flag_n = True
        
        if flag_l and flag_n:
            return True
    
    return False

def is_product_code_in_pair(row) -> bool:
    
    try:
        text_a = row['lead.name'].split()
        text_b = row['other.name']

        for t in text_a:
            # Is the string 'like' a product code and present in the other products name?
            if is_string_like_product_code(t) == True:
                if t in text_b:
                    return True

        return False
    
    except: # Defensive coding.   
        return False

def clean_mpn(mpns):
    cleaned_mpns = []
    mpns = mpns.split(',')
    for mpn in mpns:
        mpn = str(mpn).lower()
        mpn = re.sub(r'[\W_]+', '', mpn)
        cleaned_mpns.append(mpn)
    return cleaned_mpns

def partial_match(listA, listB):
    stringA = ",".join(listA) # turn list into a string with comma separated values
    partial_matches = [i for i in listB if i in stringA] # add any values in listB that are found in stringA to their own list
    if partial_matches:
        longest_match = len(max(partial_matches, key=len)) # check for length of longest match - we want it to be at least 5 characters to reduce false positives
        return longest_match
    return 0

def mpn_match(row):
    lead_mpns = row['lead.mpns']
    other_mpns = row['other.mpns']
    lead_mpn = clean_mpn(lead_mpns)
    other_mpn = clean_mpn(other_mpns)

    lead_model_nos = row['lead.model_nos']
    other_model_nos = row['other.model_nos']
    lead_model_no = clean_mpn(lead_model_nos)
    other_model_no = clean_mpn(other_model_nos)

    longest_match_case1 = partial_match(lead_mpn, other_model_no)      # other MODEL_NUMBER is in lead MPN
    longest_match_case2 = partial_match(lead_model_no, other_mpn)      # other MPN is in lead MODEL_NUMBER
    longest_match_case3 = partial_match(other_mpn, lead_model_no)      # lead MODEL_NUMBER is in other MPN
    longest_match_case4 = partial_match(other_model_no, lead_mpn)      # lead MPN is in other MODEL_NUMBER

    #full confidence if full match between...
    if (lead_mpn[0] != '' and
        (set(lead_mpn) & set(other_mpn) or          #...lead and other MPNs
        set(lead_mpn) & set(other_model_no) or      #...lead MPN and other MODEL_NUMBER
        set(lead_model_no) & set(other_mpn))        #...lead MODEL_NUMBER and other MPN
        ):
        return 1

    #partial confidence if partial match where...
    elif (lead_mpn[0] != '' and
        ((longest_match_case1 > 4) or       # check partial match is at least 5 chars
        (longest_match_case2 > 4) or
        (longest_match_case3 > 4) or     
        (longest_match_case4 > 4))        
        ):
        return 0.75 # score chosen based on the fact that a partial match is not as good as a full match, but 5 matching chars are still significant 
            
    return 0

def is_same_client(row) -> bool:
    return row['lead.client_name'] == row['other.client_name']

def match_external_id(row) -> bool:
    return row['lead.external_id'] == row['other.external_id']

def get_features(df: pd.DataFrame) -> pd.DataFrame:
    # We use the 'matching_engine_candidate_id' here to group members
    df['mpn_match'] = df.apply(mpn_match, axis=1)
    df['confidence'] = df['confidence'].astype(float)
    df['jaccard_sim_score'] = df.apply(jaccard_similarity, args=('lead.name', 'other.name'), axis=1)
    df['group_jaccard'] = df.groupby(['matching_engine_candidate_id'])['jaccard_sim_score'].transform('mean')
    df['group_xid'] = df.groupby(['matching_engine_candidate_id'])['confidence'].transform('mean')
    df['match_external_id'] = df.apply(match_external_id, axis=1)
    df['is_product_code_in_pair'] = df.apply(is_product_code_in_pair, axis=1)
    df['is_same_client'] = df.apply(is_same_client, axis=1)
    df['lead_name_word_count'] = df['lead.name'].astype(str).str.split().str.len()
    df['other_name_word_count'] = df['other.name'].astype(str).str.split().str.len()
    df['jaccard_sim_score_desc'] = df.apply(jaccard_similarity, args=('lead.description', 'other.description'), axis=1)
    df['group_jaccard_desc'] = df.groupby(['matching_engine_candidate_id'])['jaccard_sim_score_desc'].transform('mean')
    df['lead_desc_word_count'] = df['lead.description'].astype(str).str.split().str.len()
    df['other_desc_word_count'] = df['other.description'].astype(str).str.split().str.len()

    return df

def convert_bool_features_to_binary(df: pd.DataFrame) -> pd.DataFrame:
    df["match_external_id"] = df["match_external_id"].astype(int)
    df["is_product_code_in_pair"] = df["is_product_code_in_pair"].astype(int)
    df["is_same_client"] = df["is_same_client"].astype(int)
    return df

def promotion_check(x_test: pd.DataFrame, y_test: pd.DataFrame, model) -> bool:

    # Accounts the error rate of moderator decisions.
    PRECISION_MODIFIER = 0.015
    #CONFIDENCE_THRESHOLD = 0.95
    CONFIDENCE_THRESHOLD = 0.01
    #TARGET_PRECISION = 0.98
    TARGET_PRECISION = 0.01
    #LOSS_TARGET = 0.29
    LOSS_TARGET = 0.01

    loss_score = log_loss(y_test, model.predict_proba(x_test))
    log.info("Loss Score: " + str(loss_score))
    if loss_score > LOSS_TARGET:
        log.info("Loss: " + str(log_loss(y_test, model.predict_proba(x_test))))
        return False, "Log loss is > " + str(LOSS_TARGET)
    
    model_calibrated_output = np.where(model.predict_proba(x_test)[:,0]>=CONFIDENCE_THRESHOLD, 'APPROVED', 'DEFERRED')
    calibated_precision = (precision_score(y_test, model_calibrated_output, pos_label='APPROVED')) + PRECISION_MODIFIER
    log.info("Calibrated Precision: " + str(calibated_precision))
    if calibated_precision < TARGET_PRECISION: 
        return False, "Precision is <  " + str(TARGET_PRECISION)

    log.info(classification_report(y_test, model.predict(x_test), digits=4))
    return True, "All Checks Passed."

def train_model(df: pd.DataFrame):
    '''
    Input a 'clean' data frame and output a trained model.
    '''
    log.info('Data Science - Starting Model Training')
    df = get_features(df)
    df = convert_bool_features_to_binary(df)
    log.info('Data Science - Acquired Model Features')
    
    # Split data
    train_inds, test_inds = next(GroupShuffleSplit(test_size=.5, n_splits=2, random_state = 7).split(df, groups=df['matching_engine_candidate_id'].values))
    df_train = df.iloc[train_inds]
    df_test = df.iloc[test_inds]

    # Keep model features
    x_train = df_train[['confidence', 'jaccard_sim_score', 'jaccard_sim_score_desc', 'is_product_code_in_pair', 'is_same_client', 'match_external_id', 'mpn_match', 'lead_desc_word_count', 'other_desc_word_count', 'lead_name_word_count', 'other_name_word_count', 'group_xid', 'group_jaccard', 'group_jaccard_desc']]
    y_train = df_train[['decision']]
    x_test = df_test[['confidence', 'jaccard_sim_score', 'jaccard_sim_score_desc', 'is_product_code_in_pair', 'is_same_client', 'match_external_id', 'mpn_match', 'lead_desc_word_count', 'other_desc_word_count', 'lead_name_word_count', 'other_name_word_count', 'group_xid', 'group_jaccard', 'group_jaccard_desc']]
    y_test = df_test[['decision']]

    # Train
    model = GradientBoostingClassifier(n_estimators=100, max_features=7, min_samples_split = 200, max_depth=5, min_samples_leaf=45, subsample=0.9, random_state=2)
    model.fit(x_train,y_train)

    promotion_outcome, promotion_message = promotion_check(x_test, y_test, model)
    print(promotion_message)

    if promotion_outcome == False:
        log.info('Data Science - PROMOTION FAILED: Generated model does not meet promotion standards: ' + promotion_message)
        raise SystemExit('Modelling Evaluation Standards Unmet.')
    else:
        log.info('Data Science - PROMOTION PASSED: Generated model meets promotion standards.')

    return model




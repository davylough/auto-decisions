import pandas as pd
import logging
log = logging.getLogger(__name__)
import numpy as np

def remove_punctuation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning puncuation led to the output csv malforming when applied to the description.
    The attribute was left without this preprocessing as it had no material impact on model performance.
    """

    df['lead.name'] = df['lead.name'].str.replace(r'[^\w\s]+', '')
    df['other.name'] = df['other.name'].str.replace(r'[^\w\s]+', '')

    return df

def lowercase_text(df: pd.DataFrame) -> pd.DataFrame:

    df['lead.name'] = df['lead.name'].str.lower()
    df['other.name'] = df['other.name'].str.lower()
    df['lead.description'] = df['lead.description'].str.lower()
    df['other.description'] = df['other.description'].str.lower()

    return df


def get_clean_mpns(row: pd.DataFrame) -> list:
    """
    This function ingests a row containing a 'JSON-like' string.
    If it contained an MPN Key, the MPN values are returned (assumed to be a list of MPNS)
    """
    try:
        attributes = row['attrs']
        attributes = attributes.replace("{", "").replace("}", "").replace(',', '')
        attributes = attributes.replace("INVALID_MANUFACTURER_PART_NUMBER", "INVALID_MPN") # rename so that we don't accidentally match on MANUFACTURER_PART_NUMBER
        attributes = attributes.split(']')

        # Get all MPNs in a list-like format
        for pair in attributes:
            if "MANUFACTURER_PART_NUMBER" in pair:
                mpns = '[' + pair.split('[', 1)[1].split(']')[0] + ']'
                mpns = mpns.replace(" ", ", ") #add commas back in for easier extraction later
                return mpns

        return '[]' # This is a string as some of the modelling processes expect this downstream.
    except:
        log.info("Data Engineering - Something went wrong with row attributes: " + str(row['attrs'].values))
        return '[]'

def get_clean_model_nos(row: pd.DataFrame) -> list:
    """
    This function ingests a row containing a 'JSON-like' string.
    If it contained a MODEL_NUMBER Key, the model number values are returned (assumed to be a list of model numbers)
    """
    try:
        attributes = row['attrs']
        attributes = attributes.replace("{", "").replace("}", "").replace(',', '')
        attributes = attributes.split(']')

        # Get all model numbers in a list-like format
        for pair in attributes:
            if "MODEL_NUMBER" in pair:
                model_nos = '[' + pair.split('[', 1)[1].split(']')[0] + ']'
                model_nos = model_nos.replace(" ", ", ") #add commas back in for easier extraction later
                return model_nos

        return '[]' # This is a string as some of the modelling processes expect this downstream.
    except:
        log.info("Data Engineering - Something went wrong with row attributes: " + str(row['attrs'].values))
        return '[]'


def convert_not_a_number_values(df: pd.DataFrame) -> pd.DataFrame:

    df['lead.name'] = df['lead.name'].replace(np.nan, '', regex=True)
    df['other.name'] = df['other.name'].replace(np.nan, '', regex=True)
    df['lead.description'] = df['lead.description'].replace(np.nan, '', regex=True)
    df['other.description'] = df['other.description'].replace(np.nan, '', regex=True)

    return df

def create_lead_candidate_rows(df: pd.DataFrame) -> pd.DataFrame:

    df_c = df[df['member_type'] != 'lead']
    df_l = df[df['member_type'] == 'lead']

    # Rename child dataframes to reflect their role as a lead or candidate product.
    df_l = df_l[['client_name', 'matching_engine_candidate_id', 'name', 'attrs', 'member_type', 'external_id', 'mpns', 'model_nos', 'description']]
    df_l = df_l.rename(columns={'client_name': 'lead.client_name', 'name': 'lead.name', 'attrs': 'lead.attrs', 'member_type': 'lead.member_type', 'external_id': 'lead.external_id', 'mpns': 'lead.mpns', 'model_nos': 'lead.model_nos', 'description': 'lead.description',})
    df_c = df_c[['decision', 'matching_engine_candidate_id', 'confidence', 'client_name', 'name', 'attrs', 'member_type', 'external_id', 'mpns', 'model_nos', 'description']]
    df_c = df_c.rename(columns={'client_name': 'other.client_name', 'name': 'other.name', 'attrs': 'other.attrs', 'member_type': 'other.member_type', 'external_id': 'other.external_id', 'mpns': 'other.mpns', 'model_nos': 'other.model_nos', 'description': 'other.description',})
    df = pd.merge(df_c, df_l, on='matching_engine_candidate_id', how='inner')

    # Remove rows when products are lead to lead, redundant processing.
    df = df[~((df['other.member_type'] == 'lead') & (df['lead.member_type'] == 'lead'))] 
    
    return df

def preprocess_mumford_data(df: pd.DataFrame) -> pd.DataFrame:

    ROW_LIMIT = len(df)
    df = df.head(ROW_LIMIT)

    df = df[df['decision'] != 'ERRORED']
    log.info("Data Engineering - Kept Only APPROVED And REJECTED Decisions")

    df['mpns'] = df.apply(get_clean_mpns, axis=1)
    log.info("Data Engineering - Unnest the attributes object, retrieving the MPN information.")

    df['model_nos'] = df.apply(get_clean_model_nos, axis=1)
    log.info("Data Engineering - Unnest the attributes object, retrieving the Model Number information.")

    df = create_lead_candidate_rows(df)
    log.info("Data Engineering - Created lead -= candidate row wise relationship.")

    df = convert_not_a_number_values(df)
    log.info("Data Engineering - Replaced NANs for products with empty String")

    df = remove_punctuation(df)
    log.info("Data Engineering - Removed punctuation from text")

    df = lowercase_text(df)
    log.info("Data Engineering - Converted all text to lowercase")

    df['decision'] = df['decision'].map({'APPROVED':'APPROVED', 'REJECTED':'DEFERRED'})
    log.info("Data Engineering - Modified target label from REJECTED to DEFERRED")

    log.info(df['decision'].value_counts(normalize=True))
    log.info(len(df))

    return df

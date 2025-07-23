import pandas as pd

def read_excel(file_path):
    accounts = pd.read_excel(file_path, sheet_name='tai_khoan')
    keywords = pd.read_excel(file_path, sheet_name='key_word')
    return accounts, keywords

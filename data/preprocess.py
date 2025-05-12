import pandas as pd
import numpy as np

file = 'genocide_corpus.tsv'
df = pd.read_csv(file, sep='\t')
yvcdh = pd.read_parquet('yad_vashem_CdH_joint.parquet')
# print(df['COUNTRY'].unique())
yvcdhcountry = list(yvcdh.country.unique())
orgunq, orgcounts = np.unique(yvcdh.country.copy().fillna('None').tolist(), return_counts=True)
def splitter(item):
    if item and not pd.isna(item):
        if ' , ' in item:
            return ', '.join(item.upper().strip().split(' , '))
        if ', ' in item:
            return ', '.join(item.upper().strip().split(', '))
        if ' / ' in item:
            return ', '.join(item.upper().strip().split(' / '))
        if '/ ' in item:
            return ', '.join(item.upper().strip().split('/ '))
        if '/' in item:
            return ', '.join(item.upper().strip().split('/'))
        return item.upper()
    else: return item
    
yvcdh.country = yvcdh.country.apply(splitter)
df.COUNTRY = df.COUNTRY.apply(splitter)

yvcdhcountry = set(item for sublist in yvcdh.country.tolist()
                for item in (sublist if isinstance(sublist, list) else [sublist]))

country =  set(item for sublist in df.COUNTRY.tolist()
                for item in (sublist if isinstance(sublist, list) else [sublist]))

country_iso_map = {
    'BANGLADESH': 'BD', 'SOVIET UNION': 'SU', 'SE': 'SE', 'CHILE': 'CL',
    'AU ': 'AU', 'IT FR CH DE': 'IT, FR, CH, DE', 'CH': 'CH', 'DE ': 'DE',
    'NL ': 'NL', 'CROATIA': 'HR', 'VENEZUELA': 'VE', 'JAPAN': 'JP',
    'HU ': 'HU', 'MACEDONIA': 'MK', 'LITHUANIA': 'LT', 'NEW ZEALAND': 'NZ',
    'FINLAND': 'FI', 'DE/PL': 'DE, PL', 'ES ': 'ES', 'ARMENIA': 'AM',
    'DRAMA': None, 'WEST GERMANY': 'DE', 'TURKEY': 'TR', 'BG': 'BG',
    'PL/DE': 'PL, DE', 'JP': 'JP', 'US': 'US', 'AT ': 'AT',
    'CS ': 'CS', 'PARAGUAY': 'PY', 'FR/IT': 'FR, IT', 'HU': 'HU',
    'AT': 'AT', 'EAST GERMANY': 'DE', 'ALBANIA': 'AL', 'MEXICO': 'MX',
    'LT ': 'LT', 'GREECE': 'GR', None: None, 'COLOMBIA': 'CO',
    'CAMBODIA': 'KH', 'TUNISIA': 'TN', 'FR ': 'FR', 'CZECHOSLOVAKIA': 'CS',
    'PORTUGAL': 'PT', 'ESTONIA': 'EE', '?': None, 'BE ': 'BE',
    'FRANCE': 'FR', 'HONG KONG': 'HK', 'IT': 'IT', 'NO ': 'NO',
    'SU': 'SU', 'UN': 'UNITED NATIONS', 'SERBIA': 'RS', 'SLOVENIA': 'SI',
    'IL': 'IL', 'GREAT BRITAIN': 'GB', 'SE ': 'SE', 'CHINA': 'CN',
    'GE ': 'GE', 'UNITED STATES OF AMERICA': 'US', 'FI': 'FI', 'IRELAND': 'IE',
    'GB ': 'GB', 'IL [P9] ': 'IL', 'GR': 'GR', 'LU': 'LU',
    'IL ': 'IL', 'BRAZIL': 'BR', 'UKRAINE': 'UA', 'USA': 'US',
    'AUSTRIA': 'AT', 'BULGARIA': 'BG', 'MX': 'MX', 'DK': 'DK',
    'IT ': 'IT', 'PERU': 'PE', 'DENMARK': 'DK', 'GEORGIA': 'GE',
    'P9 ': 'IL', 'RUSSIA': 'RU', 'UA': 'UA', 'SOUTH AFRICA': 'ZA',
    'GB?': 'GB', 'FR': 'FR', '??': None, 'KAZAKHSTAN': 'KZ',
    'URUGUAY': 'UY', 'LATVIA': 'LV', 'CH/US': 'CH, US', 'IRAQ': 'IQ',
    'YUGOSLAVIA': 'YU', 'CANADA': 'CA', 'AR': 'AR', 'FI ': 'FI',
    'NO': 'NO', 'DK ': 'DK', 'ROMANIA': 'RO', 'KENYA': 'KE',
    'AU': 'AU', 'PHILIPPINES': 'PH', 'EG ': 'EG', 'BY': 'BY',
    'BELARUS': 'BY', 'IE ': 'IE', 'ES': 'ES', 'CSSR': 'CS',
    'AZERBAIJAN': 'AZ', 'IL?': 'IL', 'BELGIUM': 'BE', 'RWANDA': 'RW',
    'ITALY': 'IT', 'AUSTRALIA': 'AU', 'CH ': 'CH', '(GB)': 'GB',
    'THE NETHERLANDS': 'NL', 'PL ': 'PL', 'SWEDEN': 'SE', 'LUXEMBOURG': 'LU',
    'CS': 'CS', 'SWITZERLAND': 'CH', 'IE': 'IE', 'US ': 'US',
    'INDIA': 'IN', 'COSTA RICA': 'CR', 'DE': 'DE', 'ARGENTINA': 'AR',
    'CZECH REPUBLIC': 'CZ', 'PL': 'PL', 'CA': 'CA', 'KOSOVO': 'XK',
    'SPAIN': 'ES', 'P9': 'IL', 'ISRAEL': 'IL', 'NORWAY': 'NO',
    'DD': 'DE', 'FR/IL': 'FR, IL', 'IL [P9]': 'IL', 'SLOVAKIA': 'SK',
    'SYRIA': 'SY', 'NL': 'NL', 'GERMANY': 'DE', 'YU': 'YU',
    'JP ': 'JP', 'GB': 'GB', 'BE': 'BE', 'IRAN': 'IR',
    'POLAND': 'PL', 'RU': 'RU', 'BOSNIA AND HERZEGOVINA': 'BA', 'MOLDOVA': 'MD',
    'EGYPT': 'EG', 'HUNGARY': 'HU', 'WEST GERMANY': "DE", 'EAST GERMANY': "DE", 'GDR': 'DE',
}

country_iso_map2 = {
    float('nan'): None, 'nan': None, 'NAMIBIA': 'NA', 'PORTUGAL': 'PT', 'MOROCCO': 'MA',
    'LEBANON': 'LB', 'NORWAY': 'NO', 'UK': 'GB', 'SPAIN': 'ES',
    'CONGO': 'CG', 'UGANDA': 'UG', 'ISRAEL': 'IL', 'SWITZERLAND': 'CH',
    'SOUTH AFRICA': 'ZA', 'QATAR': 'QA', 'POLAND': 'PL', 'SWEDEN': 'SE',
    'CANADA': 'CA', 'HUNGARY': 'HU', ' USA': 'US', 'DENMAERK': 'DK',
    'NIGERIA': 'NG', 'CAMBODIA': 'KH', 'PALESTINE': 'PS', 'MONTENEGRO': 'ME',
    'ITALY': 'IT', 'LITHUANIA': 'LT', 'FRANCE': 'FR', 'UKRAINE': 'UA',
    'DENMARK': 'DK', 'FINLAND': 'FI', 'SOUTH  AFRICA': 'ZA', 'GERMANY': 'DE',
    'KENYA': 'KE', 'EAST GERMANY': 'DE', ' FRANCE': 'FR', 'AUSTRIA ': 'AT',
    'AUSTRIA': 'AT', 'BELGIUM': 'BE', 'NEW ZEALAND': 'NZ', 'BANGLADESH': 'BD',
    'LUXEMBOURG': 'LU', 'NETHERLANDS': 'NL', 'FRANCE ': 'FR', 'SERBIA': 'RS',
    'USSR': 'SU', 'BOSNIA AND HERZEGOVINA': 'BA', ' SERBIA': 'RS', 'ARGENTINA': 'AR',
    'GEORGIA': 'GE', 'INDONESIA': 'ID', 'SWISS': 'CH', 'MALAYSIA': 'MY',
    'PAKISTAN': 'PK', 'BURMA': 'MM', 'CZECH REPUBLIC': 'CZ', 'YUGOSLAVIA': 'YU',
    'ICTY_VARIOUS': 'ICTY', 'CHILE': 'CL', 'CHINA': 'CN', 'IRELAND': 'IE',
    'WEST GERMANY': 'DE', 'SLOVENIA': 'SI', 'CROATIA': 'HR', 'GDR': 'DE',
    'LATVIA': 'LV', 'GEEMANY': 'DE', 'AUSTRALIA': 'AU', 'UNITED NATIONS': 'UNITED NATIONS',
    'NAMIBIA ': 'NA', 'RWANDA': 'RW', 'US': 'US', 'USA': 'US',
    'ARMENIA': 'AM', 'BOSNIA': 'BA'
}

df.COUNTRY = df.COUNTRY.apply(lambda x: country_iso_map2.get(x) if isinstance(str(x).split(', '), str) else ', '.join([str(country_iso_map2.get(subitem)) for subitem in str(x).split(', ') ]))
yvcdh.country = yvcdh.country.apply(lambda x: country_iso_map.get(x) if isinstance(str(x).split(', '), str) 
       else ', '.join([str(country_iso_map.get(subitem)) for subitem in str(x).split(', ') ]))


# unq, counts = np.unique(yvcdh.country.tolist(), return_counts=True)
# unq, counts = np.unique(df.COUNTRY.tolist(), return_counts=True)
# print(list(zip(unq,counts)))
# print(list(zip(orgunq, orgcounts)))

df.to_parquet('genocide_corpus.parquet')
yvcdh.to_parquet('yad_vashem_CdH_joint.parquet')
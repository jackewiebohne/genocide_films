import pandas as pd
import numpy as np
import string, re

### TODO: preprocess the data more and clean it up. remove tags and newline chars

class yvcdh_handler():
    def __init__(self, datapath):
        self.__name__ = 'yvcdh'
        self.timeaxis = 'year'
        self.numeric_axes = ['year', 'duration']
        self.datapath = datapath
        self.df = pd.read_parquet(self.datapath)
        self.strcols = 'summary title producer country genre color language distributor further_production_info director other_title'.split()\
                        + ['production company', 'data_source']
        self.df.year = pd.to_numeric(self.df.year, errors='coerce')
        self.df.duration = pd.to_numeric(self.df.duration, errors='coerce')

    def search(self, searchinput, dates, duration, search_col=['summary'], case=False, **cond_kwargs):

        if not isinstance(search_col, list): search_col = [search_col]

        if not set(search_col).intersection(set(self.df.columns)) and not search_col[0]=='all':
            raise ValueError('Column not contained in the data. Enter one of:  ', self.strcols + ['all'], '. You entered: ', search_col)
        
        elif search_col[0] == 'all':
            search_col = self.strcols

        # if cond_kwargs:
        #     ## flexible handling of additional conditions
        #     ## where k is the column and v the value the df has to be equal to in k
        #     ## all the conditions are logically chained with & (i.e. all conditions have to be met)
        #     mask = np.all(np.column_stack([(self.df[k] == v).values for k, v in cond_kwargs.items()]) > 0, axis=1)
        #     search = self.df[mask & self.df.duration.isin(duration) & 
        #                      self.df.loc[self.df.year.isin(dates), search_col]
        #                      .apply(lambda x: x.replace('[^\w\s]', '')
        #                             .str.contains(searchinput, na=False, case=case, regex=True)).any(axis=1)]

        # else:
        #     search = self.df[self.df.duration.isin(duration) & 
        #                      self.df.loc[self.df.year.isin(dates), search_col]
        #                      .apply(lambda x: x.replace('[^\w\s]', '')
        #                             .str.contains(searchinput, na=False, case=case, regex=True)).any(axis=1)]
        
        ## flexible handling of additional conditions
        ## where k is the column and v the value the df has to be equal to in k
        ## all the conditions are logically chained with & (i.e. all conditions have to be met)
        if cond_kwargs: mask = np.all(np.column_stack([(self.df[k] == v).values for k, v in cond_kwargs.items()]) > 0, axis=1)
        else: mask = np.ones(len(self.df))

        def _return_regex_finds_df(row):
            if not case:
                found = set()
                any(found.update(set(re.findall(searchinput, row[c].lower(), flags=re.IGNORECASE))) for c in row.index)
                return '|'.join(sorted(list(found))) if found else pd.NA
            else:
                found = set()
                any(found.update(set(re.findall(searchinput, row[c]))) for c in row.index)
                return '|'.join(sorted(list(found))) if found else pd.NA

        def _return_regex_finds_series(series):
            if not case: 
                return series.str.lower().str.findall(searchinput, flags=re.IGNORECASE).apply(lambda x: '|'.join(sorted(list(set(x)))))
            else: 
                return series.str.findall(searchinput).apply(lambda x: '|'.join(sorted(list(set(x)))))

        copy = self.df.copy()
        if search_col == self.strcols:
            copy.loc[:, 'searchterm'] = copy.loc[mask & copy.duration.isin(duration) & copy.year.isin(dates), search_col]\
                                 .fillna('').apply(_return_regex_finds_df, axis=1)
        else: 
            copy.loc[:, 'searchterm'] = copy.loc[mask & copy.duration.isin(duration) & copy.year.isin(dates), search_col]\
                     .fillna('').apply(_return_regex_finds_series)

        search = copy[copy.searchterm.fillna('').map(len)>0]
        search.drop(columns=['normalisedtitle'], inplace=True)
        search = search.sort_values('year')
        del copy
        return search

    def render_context(self):
        # function to show context windows around search terms?
        pass


        

# h = yvcdh_handler('https://raw.githubusercontent.com/jackewiebohne/genocide_films/main/data/yad_vashem_CdH_joint.tsv')
# # print(h.df.groupby(['year', 'genre'])[['country','duration']].agg({'country':'size', 'duration':'sum'}).reset_index().rename(columns={'country': 'num_country', 'duration': 'sum_duration'})#.reset_index(name=['num_country', 'sum_duration']))
# searchout = h.search('hitler|himmler', list(range(1900, 2020)), list(range(0,2000)), ['all']) #, **{'director':'Claude Lanzmann'})) 
# print(searchout)
# for e in searchout.searchterm:
#     print(e)
# print(h.df.groupby(['country'])[['year', 'duration']])

import pandas as pd
import numpy as np
import string, re

class mycorp_handler():
    def __init__(self, datapath):
        self.__name__ = 'mycorp'
        self.timeaxis ='DATE'
        self.numeric_axes = ['DATE', 'DURATION']
        self.datapath = datapath
        self.df = pd.read_csv(self.datapath, sep='\t')
        self.df.drop(columns=['DATA STATE', 'ACQUIRED', 'DOC TYPE'], inplace=True)
        self.df.rename(columns={'ATROCITY, GENOCIDE': 'ATROCITY', 'PERP GENDER': 'PERP_REPRESENTED_GENDER', 
                                'PERP REPR': 'PERP_REPRESENTATION', 'PERP GROUPS': 'PERP_GROUPS', 'COLLABORATOR GROUPS': 'COLLABORATOR_GROUPS',
                                'VICTIM REPR': 'VICTIM_REPR', 'VICTIM GROUPS':'VICTIM_GROUPS', "VICTIM GENDER INTERVIEWS":'VICTIM_GENDER_INTERVIEWS',
                                'SEXUAL VIOLENCE': 'SEXUAL_VIOLENCE', 'VIOLENCE RATIONALE/CAUSES': 'VIOLENCE_CAUSES'}, inplace=True)
        self.strcols = [c for c in self.df.columns if not c in ('DATE', 'DURATION', 'SEXUAL_VIOLENCE', 'RATINGS')]
        self.df.DATE = pd.to_numeric(self.df.DATE, errors='coerce')
        self.df.DURATION = pd.to_numeric(self.df.DURATION, errors='coerce')
        self.rename_map = {'Herero & Nama':"Herero & Nama g.", 'Armenia':'Armenian g.', 
                            'Holodomor':'Holodomor', 'Holocaust':'Holocaust', 
                            'Indonesia':'Indonesian g.', 'Cambodia': 'Cambodian g.','Rwanda':'Rwandan g.','Bosnia':'Bosnian g.'}
        self.df['ATROCITY'] = self.df['ATROCITY'].map(self.rename_map)
        any(self._standardise_col(c, ', ') for c in ('COUNTRY', 'LANGUAGE', 'VICTIM_GENDER_INTERVIEWS', 'PERP_REPRESENTED_GENDER')) 
        ## check unique vals in the above cols, also check sexual vioelnce col unique vals

    def _standardise_col(self, col, sep):
        self.df.loc[:, col] = self.df.loc[:, col].apply(lambda x: ', '.join(sorted(x.lower().split(sep))) if isinstance(x, str) else np.nan)

    def search(self, searchinput, dates, duration, search_col=['COMMENTS'], case=False, **cond_kwargs):
        
        if not isinstance(search_col, list): search_col = [search_col]

        if not set(search_col).intersection(set(self.df.columns)) and not search_col[0]=='all':
            raise ValueError('Column not contained in the data. Enter one of:  ', self.strcols + ['all'], '. You entered: ', search_col)
        
        elif search_col[0] == 'all':
            search_col = self.strcols

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
            copy.loc[:, 'searchterm'] = copy.loc[mask & copy.DURATION.isin(duration) & copy.DATE.isin(dates), search_col]\
                                 .fillna('').apply(_return_regex_finds_df, axis=1)
        else: 
            copy.loc[:, 'searchterm'] = copy.loc[mask & copy.DURATION.isin(duration) & copy.DATE.isin(dates), search_col]\
                     .fillna('').apply(_return_regex_finds_series)

        search = copy[copy.searchterm.fillna('').map(len)>0]
        search = search.sort_values('DATE')
        del copy
        return search

    def render_context(self):
        # function to show context windows around search terms?
        pass



    
# h = mycorp_handler('https://raw.githubusercontent.com/jackewiebohne/genocide_films/main/data/genocide_corpus.tsv')
# print(h.search('hitler', list(range(1900, 2020)), list(range(0,2000)), search_col='COMMENTS')) # 'summary', False, , **{'DIRECTOR':'Lanzmann'}
 

# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 06:22:17 2021

@author: ehom4
"""
#%%
import datetime 
import pandas as pd 
import os 
import numpy as np 
# import argparse
# import ffn 
#%%
def convert_jd(jd:str):
    '''轉換儒略日 '''
    if int(jd) == 0:
        return 
    try:
        date = datetime.date(1899,12,29) + datetime.timedelta(days=int(jd))
        return date 
    except OverflowError as e:
        return 
    
def parse_pl_file(filename):
    ''' 讀取x5績效表單(PL-*.txt)成資料表格式 (pd.dataframe)
    '''
    data = {}
    with open(filename,encoding='cp950') as f: 
        for idx,line in enumerate(f):
            
            jtime,others=line.split('=')
            jtime = convert_jd(jtime)
            
            open_profit_byATR = others[:others.find('_')]
            
            others = others[others.find('_')+1:]
            one_day_before_entry, today_exit_nums,*others = others.split('#')
            
            
            data[jtime] = {
                            'open_profit_byATR' : float(open_profit_byATR),
                            'day_before_entry' : convert_jd(one_day_before_entry),
                            'today_exit_nums' : int(today_exit_nums),
                    }
            
            tmp_dict = {}
            for idx,c in enumerate(others):
                closed_str = 'closed_profit_byATR_{}'.format(idx+1)
                closed_str_date = 'day_before_entry_{}'.format(idx+1)
                            
                closed_profit_byATR = c[:c.find('_')].strip()
                one_day_before_entry_closed = c[c.find('_')+1:].strip()
                if closed_profit_byATR and one_day_before_entry_closed:
                    tmp_dict[closed_str] = float(closed_profit_byATR)
                    tmp_dict[closed_str_date] = convert_jd(one_day_before_entry_closed)
                
            data[jtime].update(tmp_dict)
    df = pd.DataFrame(data)
    df = df.T 
    df.index = pd.DatetimeIndex(df.index)
    return df 


def cal_profit(df,riskR=0.003):
    '''calculate singel asset closed & open pnl 
    
        1) closed profit 
        2) open profit 
    '''
    sel_cols = []
    sel_cols1 = []
    for e in list(df.columns):
        len_of_nums = -1*len(e.split('_')[-1]) - 1
        if e[:len_of_nums] == 'closed_profit_byATR' : sel_cols.append(e)
        if e[:len_of_nums] == 'day_before_entry': sel_cols1.append(e)
    df['closed_pnl_byATR'] = df[sel_cols].sum(axis=1)    
    df['closed_pnl'] = (df.closed_pnl_byATR*riskR).cumsum() + 1
    df['open_pnl'] = df.open_profit_byATR*riskR + df.closed_pnl 
    
    df = df.astype({
            'open_profit_byATR':float,
            'today_exit_nums':int,
            'day_before_entry':'datetime64[ns]',
            'closed_pnl_byATR':float,
            'closed_pnl':float,
            'open_pnl': float
                    }) 
    df[sel_cols] = df[sel_cols].astype(float)
    df[sel_cols1] = df[sel_cols1].astype('datetime64[ns]')
    df['riskR'] = riskR
    return df

def cal_portfolio_profit(dfs):
    '''

    Parameters
    ----------
    dfs : list of dataframe 
        

    Returns
    -------
    protfolio profit (with open pnl)

    '''
    _idx = np.argmax([len(df) for df in dfs])
    closed_pnl = pd.Series(0,index=dfs[_idx].index)
    open_pnl = closed_pnl.copy()
    # closed_pnl = (dfs[0]['riskR']*dfs[0]['closed_pnl_byATR']).fillna(0)
    # open_pnl = (dfs[0]['riskR']*dfs[0]['open_profit_byATR']).fillna(0)
    for idx,df in enumerate(dfs):

        closed_pnl += df['riskR']*df['closed_pnl_byATR'].fillna(0)
        open_pnl += df['riskR']*df['open_profit_byATR'].fillna(0)
    closed_pnl = closed_pnl.fillna(0)
    open_pnl = open_pnl.fillna(0)
    return (1+closed_pnl.cumsum() + open_pnl).ffill()
    
#%%1. 比較一種價格圖結果
if __name__ == '__main__':
    
    filename = 'PL-3001_YM_1_60_1_0.txt'
    df = parse_pl_file(filename)
    df = cal_profit(df, riskR=0.01)
    df.to_csv('portfolio-test.csv')
    
#%% 2.比較兩種價格圖
    filenames = ['PL-3001_YM_1_60_1_0.txt','PL-3001_YM_1_240_1_0.txt']    
    dfs = []
    for file in filenames :
        df = parse_pl_file(file)
        df = cal_profit(df,riskR=0.01)
        dfs.append(df)
    pnl = cal_portfolio_profit(dfs)
    pnl.to_csv('portfolio-test-2.csv',header=None)
#%% 3. 讀取資料夾底下(read all PL-*.txt )=> 測試四種價格圖
    dfs = []
    for file in os.listdir():
        if file[-3:]=='txt' and file[:2]=='PL':
            df = parse_pl_file(file)
            df = cal_profit(df,riskR=0.01)
            dfs.append(df)
    
    pnl_tot = cal_portfolio_profit(dfs)
    pnl_tot.to_csv('portfolio-test-tot.csv',header=None)
#%%

    


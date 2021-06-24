# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 06:22:17 2021

@author: ehom4
"""
#%% module 
import datetime 
import pandas as pd 
import os 
import numpy as np 
# import argparse
import ffn 
#%% function
def convert_jd(jd:str):
    '''轉換儒略日 '''
    if int(jd) == 0:
        return 
    try:
        date = datetime.date(1900,1,1) + datetime.timedelta(days=int(jd))
        return date 
    except OverflowError as e:
        return 
    
def parse_pl_file(filename:str):
    '''
    讀取x5績效表單(PL-*.txt)成資料表格式 (pd.dataframe)

    Parameters
    ----------
    filename : str
        

    Returns
    -------
    df : pd.DataFrame
        

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

def cal_portfolio_profit(dfs,resetDays=365):
    '''calculate portfolio equity 

    Parameters
    ----------
    dfs : list of dataframe 
    resetDays: rebalance day, 
        : -1 = do not rebalance asset
    
        

    Returns
    -------
    protfolio profit (with open pnl)

    '''    
    
    
    cl_r_atrs = [df['riskR']*df['closed_pnl_byATR'] for df in dfs]
    closed_pnl = pd.concat(cl_r_atrs,axis=1).pipe(np.sum,axis=1)
    ol_r_atrs = [df['riskR']*df['open_profit_byATR'] for df in dfs]
    open_pnl = pd.concat(ol_r_atrs,axis=1).pipe(np.sum,axis=1)
    
    
    
    if resetDays != -1: 
        resetDays_ = str(resetDays)+'D'
        dates =  closed_pnl.resample(resetDays_).last().index
    else:        
        pass
    
    
        
    
    ''' (rebalance) reset equity
    '''
    
    
    c_pnl = pd.Series(0.0,index=closed_pnl.index)    
    o_pnl = c_pnl.copy()
    # dates = pd.to_datetime((closed_pnl.index)).resample(resetDays_).last().index
    if resetDays != -1:
        r = 1 
        for sdate,edate in zip(dates,dates[1:]):
            c_pnl[sdate:edate] = r*(1+closed_pnl[sdate:edate].cumsum())
            o_pnl[sdate:edate] = r*open_pnl[sdate:edate]
            r *= (1+closed_pnl[sdate:edate].cumsum().iloc[-1])
            
    
        c_pnl[edate:] = r*(1+closed_pnl[edate:].cumsum())
        o_pnl[edate:] = r*open_pnl[edate:]
        
    elif resetDays == -1:
        c_pnl = (1+closed_pnl.cumsum())
        o_pnl = open_pnl
        
    
    return c_pnl+o_pnl

def cal_mar(pnl:pd.Series):
    '''
    calculate MAR value 

    Parameters
    ----------
    pnl : pd.Series
        profit and loss time series 

    Returns
    -------
    dictionary 
        key: cagr, mdd, mar

    '''
    cagr = ffn.core.calc_cagr(pnl)
    mdd = ffn.core.calc_max_drawdown(pnl)
    mar = cagr/abs(mdd)
    return {'CAGR':cagr,'MDD':mdd,'MAR':mar}
#%%1. 比較一種價格圖結果
if __name__ == '__main__':
    
    pl_directory = 'pl-data'
    
    if not os.path.exists(pl_directory):
        os.makedirs(pl_directory )
    
    filename = 'PL-3001_YM_1_60_1_0.txt'
    filename = os.path.join(pl_directory,filename)    
    df = parse_pl_file(filename)
    df = cal_profit(df, riskR=0.01)
    pnl1 = cal_portfolio_profit([df])
    # df.to_csv('portfolio-test-1.csv')
    # pnl1.to_csv('portfolio-test-1-r.csv')
#%% 2.比較兩種價格圖
    filenames = ['PL-3001_YM_1_60_1_0.txt','PL-3001_YM_1_240_1_0.txt']    
    dfs = []
    for file in filenames :
        file = os.path.join(pl_directory,file)
        df = parse_pl_file(file)
        df = cal_profit(df,riskR=0.01)
        dfs.append(df)
    pnl2 = cal_portfolio_profit(dfs)
    # pnl2.to_csv('portfolio-test-2-r.csv',header=None)
#%% 3. 讀取資料夾底下(read all PL-*.txt )=> 測試四種價格圖
    dfs = []
    charts = []
    for file in os.listdir(pl_directory):
        if file[-3:]=='txt' and file[:2]=='PL':
            charts.append(file)
            file = os.path.join(pl_directory,file)
            df = parse_pl_file(file)
            df = cal_profit(df,riskR=0.01)
            dfs.append(df)
            
    pnl_tot = cal_portfolio_profit(dfs,resetDays=365)
    pnl_tot_no_reset= cal_portfolio_profit(dfs,resetDays=-1)
    
    result = pd.concat([df.open_pnl for df in dfs],axis=1)
    result.columns = charts
    corr = result.corr()
    
    # pnl_tot.to_csv('portfolio-test-tot-r.csv',header=None)

#%% Plot correlation heatmap & equity curve

    import seaborn as sns 
    sns.heatmap(corr)
    # result['pnl_total'] = pnl_tot_no_reset
    


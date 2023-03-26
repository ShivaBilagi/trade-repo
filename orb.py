import numpy as np
import pandas as pd
import datetime

class ORB_backtest:
    
    """
    This module is used to back test the Opening range breakout strategy given the historical data of stocks. 
    
    Parameters:
    -----------
    
    high_col: (str)
        Column name representing high value of the candle.
        
    low_col: (str)
        Column name representing low value of the candle.
        
    close_col: (str)
        Column name representing close value of the candle.
        
    datetime_col: (str)
        Column name representing datetime of the candle.
        
    date_col: (str)
        Column name representing only date of the candle.
    
    units: (int)
        Number of units(price) to set trade profit and stop loss.
        
    profit: (int)
        Multiple of units to get trade profit. e.g: 3*50(profit*units)
        
    loss: (int)
        Multiple of units to get stop loss. e.g: 3*50(loss*units)
        
    quantity: (int)
        Quantity of shares to be traded.
        
    Returns:
    ---------
    
    DataFrame: Returns a pandas dataframe with the following columns for each day:
               ['date', 'first_high', 'first_low', 'execute_time', 'execute_price', 'out_time', 'out_price', 'profit_loss']
    
    """
    
    def __init__(self, high_col:str, low_col:str, close_col:str, datetime_col:str, date_col:str, units:int, profit:int, loss:int, quantity:int):
        self.high_col = high_col
        self.low_col = low_col
        self.close_col = close_col
        self.datetime_col = datetime_col
        self.date_col = date_col
        self.units = units
        self.profit = profit
        self.loss = loss
        self.quantity = quantity 
        
    def _transform(self, df):
        
        first_high = []; date = []; first_low = []; execute_time = []; execute_price = []; out_time = []; out_price = []; profit_loss = []
        date_input = df[self.date_col].drop_duplicates()
        
        for ind,i in enumerate(date_input):
            day_data = df[df[self.date_col] == i].sort_values(by=[self.datetime_col]).reset_index(drop=True)
            day_data["first_high"] = day_data.high[0]
            day_data["first_low"] =  day_data.low[0]
            
            date.append(i)
            first_high.append(day_data.high[0])
            first_low.append(day_data.low[0])
            
            day_data["execute_time"] = np.where((day_data[self.datetime_col]!=day_data[self.datetime_col][0])&((day_data.first_high<=day_data[self.close_col])|(day_data.first_low>=day_data[self.close_col])),day_data[self.datetime_col].dt.time,None)
            valid_execute = day_data["execute_time"].first_valid_index()
            
            if valid_execute is not None:
                execute_time.append(day_data.loc[valid_execute]["execute_time"])
                execute_price.append(day_data.loc[valid_execute][self.close_col])
                
                if execute_price[ind]>=first_high[ind]:
                    trade_profit = execute_price[ind] + self.units*self.profit
                    stop_loss = execute_price[ind] - self.units*self.loss
                    day_data["out_time"] = np.where((day_data[self.datetime_col]>day_data.loc[valid_execute][self.datetime_col])&((day_data[self.high_col]>=trade_profit)|(day_data[self.low_col]<=stop_loss)),day_data[self.datetime_col].dt.time,None)
                    valid_out = day_data["out_time"].first_valid_index()
                    
                    if valid_out is not None:
                        out_time.append(day_data.loc[valid_out]["out_time"])
                        if day_data.loc[valid_out][self.high_col] >= trade_profit:
                            out_price.append(trade_profit)
                        elif day_data.loc[valid_out][self.low_col] <= stop_loss:
                            out_price.append(stop_loss)
                    else:
                        out_time.append(day_data[self.datetime_col].dt.time.iloc[-1])
                        out_price.append(day_data[self.close_col].iloc[-1])
                        
                elif execute_price[ind]<=first_low[ind]:
                    trade_profit = execute_price[ind] - self.units*self.profit
                    stop_loss = execute_price[ind] + self.units*self.loss
                    day_data["out_time"] = np.where((day_data[self.datetime_col]>day_data.loc[valid_execute][self.datetime_col])&((day_data[self.low_col]<=trade_profit)|(day_data[self.high_col]>=stop_loss)),day_data[self.datetime_col].dt.time,None)
                    valid_out = day_data["out_time"].first_valid_index()
                    
                    if valid_out is not None:
                        out_time.append(day_data.loc[valid_out]["out_time"])
                        if day_data.loc[valid_out][self.low_col] <= trade_profit:
                            out_price.append(trade_profit)
                        elif day_data.loc[valid_out][self.high_col] >= stop_loss:
                            out_price.append(stop_loss)
                    else:
                        out_time.append(day_data[self.datetime_col].dt.time.iloc[-1])
                        out_price.append(day_data[self.close_col].iloc[-1])
                        
                if execute_price[ind] >= first_high[ind]:
                    profit_loss.append(out_price[ind] - execute_price[ind])
                elif execute_price[ind] <= first_low[ind]:
                    profit_loss.append(execute_price[ind] - out_price[ind])
                    
            else:
                execute_time.append(None)
                execute_price.append(None)
                out_time.append(None)
                out_price.append(None)
                profit_loss.append(None)
                
        result = pd.DataFrame({"date":date, "first_high":first_high, "first_low":first_low
                     , "execute_time":execute_time, "execute_price":execute_price
                     , "out_time":out_time, "out_price":out_price, "profit_loss":profit_loss})
        result["profit_loss"] = result["profit_loss"]*self.quantity
        return result
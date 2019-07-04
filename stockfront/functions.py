
import pandas as pd
import sqlalchemy

# Different functions I use, mostly realted to db an data fetcing

def get_iex_quotes(tickers, apikey):
    
    #Get the latest quotes for the tickers in the list. Used for the gapscanner.
    

    
    index = 0
    stock_quotes_final = pd.DataFrame()
    while index <len(tickers):
        
        symbols = ""
        for ticker in list(tickers)[index:index+100]:
            symbols = symbols+","+ticker
    
        str_tickers = symbols[1:]
    

        stock_quotes = pd.read_json("https://cloud.iexapis.com/beta/stock/market/batch?symbols="+str_tickers+"&types=quote&token="+apikey)
           
        #Transpose df for the loop
        stock_quotes = stock_quotes.transpose()
        
        for key, element in stock_quotes.iterrows():
            

            stock_data_temp = pd.Series(element[0]).to_frame()
            stock_data_temp = stock_data_temp.transpose()
            
            stock_data_temp.rename(columns={"symbol":"ticker"}, inplace=True)
            
            stock_quotes_final = stock_quotes_final.append(stock_data_temp)
            
        index += 100
    
    return stock_quotes_final 


#Read data from db
def read_from_database(query, serverSite):    
    #Creating the sqlalchemy engine and read sample data.
    engine = sqlalchemy.create_engine(serverSite)
    fetchedData = pd.read_sql(query, engine)    
    engine.dispose()
    return fetchedData


#Write data to db
def write_data_to_sql(df, table_name, serverSite, if_exists = "replace"):
    #you need mysql alchemy and pymysql to run this. syntax is:  Username:password@host:port/database
    engine = sqlalchemy.create_engine(serverSite)
    #Writing the data, name is table name. 
    df.to_sql(name = table_name, con = engine,index = False,  if_exists = if_exists)
    engine.dispose()

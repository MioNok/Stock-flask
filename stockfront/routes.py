from flask import Flask , jsonify, flash, redirect , render_template, request
from stockfront.forms import RegistrationForm, LoginForm, SearchForm, WLForm
from flask import session, redirect, current_app
from stockfront.models import User, Upvote, WatchlistStock, ApiToken
from stockfront import app , db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
import sqlalchemy
import pandas as pd
import stockfront.functions as func
import sys
import json
from datetime import datetime
import uuid



#Globals, TODO add these as env variables?
serverSite = 'serversiteURIstockdata'
serverSiteUser = 'serversiteURIuserdata'
iexKey = "<iexKEy>"


tickers = list(func.read_from_database("SELECT distinct ticker from dailydata; ", serverSite).ticker)


      

@app.route('/testcharts')
def chart2():
  testdata = func.read_from_database("SELECT ticker, date, uOpen, uHigh, uLow, uClose from dailydata WHERE ticker = 'AAPL' LIMIT 30; ", serverSite)
  data = []
  for row in testdata.iterrows():
      tempdict = {"x": row[1].date,
                "y": [row[1].uOpen,row[1].uHigh,row[1].uLow,row[1].uClose]}
    
      data.append(tempdict)
  
  return render_template('testing.html', datas=json.dumps(data))


@app.route('/about')
@login_required
def about():
  return render_template('about.html')


@app.route('/getgappers')
@login_required
def gap_data():
  
  history = func.read_from_database("SELECT ticker, companyName, close, latestSource,  ROUND (extendedChangePercent * 100,2) as percentChange from latestquotes WHERE extendedChangePercent > 0 ORDER BY extendedChangePercent DESC LIMIT 20 ", serverSite)
  history["link"] = "stocks/"+history.ticker
  history["watchlist"] = "watchlist/gapper/"+history.ticker
  history["upvote"] = "upvote/gapper/"+history.ticker 
  
  mydata = dict({"data":history.to_dict('records')})
  return jsonify(mydata)


@app.route('/getgappersshort')
@login_required
def gap_data_short():
  history = func.read_from_database("SELECT ticker, companyName, close, latestSource,  ROUND (extendedChangePercent * 100,2) as percentChange from latestquotes WHERE extendedChangePercent < 0 ORDER BY extendedChangePercent LIMIT 20 ", serverSite)
  history["link"] = "stocks/"+history.ticker
  history["watchlist"] = "watchlist/gapper/"+history.ticker
  history["upvote"] = "upvote/gapper/"+history.ticker 
  
  mydata = dict({"data":history.to_dict('records')})
  return jsonify(mydata)




@app.route('/getupvotes')
def gap_data_upvote():
  upvote_data = func.read_from_database("SELECT ticker, COUNT(ticker) as tickersum  from upvote WHERE DATE(date_posted) = DATE(NOW()) GROUP BY ticker ORDER BY tickersum DESC ;",serverSiteUser)
  upvote_data["place"] = upvote_data.index +1
  upvote_data["link"] = "stocks/"+upvote_data.ticker
  upvote_data["watchlist"] = "watchlist/home/"+upvote_data.ticker
  upvote_data["upvote"] = "upvote/home/"+upvote_data.ticker 
  
  mydata = dict({"data":upvote_data.to_dict('records')})
  return jsonify(mydata)





@app.route('/wldata')
@login_required
def wl_data():
  
  #Look up the wl
  wl = func.read_from_database("SELECT ticker, date_posted, scanner from watchlist_stock WHERE DATE(date_posted) = DATE(NOW()) AND user_id ="+ str(current_user.id)+"  GROUP BY ticker", serverSiteUser)

  #Get latest data for wl tickers
  latest_close = []
  for stock in wl.ticker.tolist():
    latest_close.append(func.read_from_database("SELECT close from dailydata WHERE ticker = '"+ stock + "' ORDER BY date DESC LIMIT 1 ", serverSite).iloc[0,0])

  wl["close"] = latest_close
  mydata= dict({"data":wl.to_dict('records')})

  return jsonify(mydata)


#Landing page
@app.route('/')
def landing_page():

  return render_template("landingpage.html")

#Temporary here..  
newsdata= pd.read_json("https://cloud.iexapis.com/stable/stock/AAPL/news/last/4?token="+iexKey)


#Main page
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():


  #Market sentiment data for graph
  bears = func.read_from_database("SELECT * FROM bearcounter;" , serverSite).iloc[0,0]
  bulls = 7-bears
  pcvalues = [bulls,bears]
  pclabels = ["Bull","Bear"]

  #Trade algo data
  #Portfolio data
  portvalues = func.read_from_database("Select * from portvalues", serverSite)
  portvaluesCharlie = portvalues.loc[portvalues["code"] == "Charlie"].sort_values(by = ["timestamp"])
  portvaluesDelta = portvalues.loc[portvalues["code"] == "Delta"].sort_values(by = ["timestamp"])
  portvaluesEcho = portvalues.loc[portvalues["code"] == "Echo"].sort_values(by = ["timestamp"])

  #Last trade
  charlielast = func.read_from_database("Select * from tradehistory order by timestamp desc limit 1;", serverSite)
  deltalast = func.read_from_database("Select * from tradehistory_delta order by timestamp desc limit 1;", serverSite)
  echolast = func.read_from_database("Select * from tradehistory_echo order by timestamp desc limit 1;", serverSite)




  #newsdata= pd.read_csv("https://stocknewsapi.com/api/v1?tickers=AAPL&items=4&token=gkbdbpnccgbbxdxadxs3iijjyvx5pxjdyup1zhcd&datatype=csv")
  #bannerdata_df = func.get_iex_quotes(["SPX","QQQ","DIA","HJPX","DAX","PRF"],iexKey) 
  #banner_string = ""     
  #for item in bannerdata_df.iterrows():
  #    banner_string = banner_string + str(str(item[1].ticker)+" " + str(round(item[1].change,2))+"% "+ " $"+str(round(item[1].latestPrice,2)))

  form1 = SearchForm()
  form2 = WLForm()
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("home2.html", pcvalues= pcvalues, pclabels = json.dumps(pclabels), form1 = form1, form2 = form2, newsdata = newsdata, 
                                portvaluesCharlie = portvaluesCharlie, portvaluesDelta = portvaluesDelta,  portvaluesEcho =  portvaluesEcho, 
                                charlielast = charlielast, deltalast= deltalast, echolast = echolast)

  if  form2.validate_on_submit():
      ticker= form2.ticker.data
      print("Added", ticker, "to watchlist", file=sys.stderr)
      if ticker in tickers:
        return redirect('/watchlist/own/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("home2.html", pcvalues= pcvalues, pclabels = json.dumps(pclabels), form1 = form1, form2 = form2,  newsdata = newsdata,
                                portvaluesCharlie = portvaluesCharlie, portvaluesDelta = portvaluesDelta,  portvaluesEcho =  portvaluesEcho, 
                                charlielast = charlielast, deltalast= deltalast, echolast = echolast)


  return render_template("home2.html", pcvalues= pcvalues, pclabels = json.dumps(pclabels),  form1 = form1, form2 = form2, newsdata = newsdata,
                          portvaluesCharlie = portvaluesCharlie, portvaluesDelta = portvaluesDelta,  portvaluesEcho =  portvaluesEcho, 
                          charlielast = charlielast, deltalast= deltalast, echolast = echolast)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect ("home")
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(firstname = form.firstname.data, 
                    lastname = form.lastname.data,
                    email = form.email.data,
                    password = hashed_password)

        db.session.add(user)
        db.session.commit()
        flash("Account created for "+ str(form.firstname.data) +", you can now log in!", 'success')
        return redirect("login")
    return render_template('register.html', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect ("home")
    form = LoginForm()
    if form.validate_on_submit():
      user = User.query.filter_by(email=form.email.data).first()
      if user and bcrypt.check_password_hash(user.password, form.password.data):
          login_user(user, remember = form.remember.data)
          return redirect("home")
      else:
          flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
  logout_user()
  return redirect("login")

@app.errorhandler(404)
def page_not_found(e):

  return render_template('404.html'), 404

@app.route('/week52',methods=['GET', 'POST'])
@login_required
def week52():

  form1 = SearchForm()
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("week52.html", title = "Week52", form1 = form1)

  return render_template("week52.html", title = "Week52",form1 = form1)


@app.route('/getweek52high')
@login_required
def gap_week52_high():
  history = func.read_from_database("SELECT ticker, companyName, close, week52High,  previousClose from hightickers ORDER BY extendedChangePercent DESC LIMIT 20 ", serverSite)
  history["link"] = "stocks/"+history.ticker
  history["watchlist"] = "watchlist/52week/"+history.ticker
  history["upvote"] = "upvote/52week/"+history.ticker 
  
  mydata = dict({"data":history.to_dict('records')})
  return jsonify(mydata)


@app.route('/getweek52low')
def gap_week52_low():
  history = func.read_from_database("SELECT ticker, companyName, close, week52Low,  previousClose from lowtickers ORDER BY extendedChangePercent DESC LIMIT 20 ", serverSite)
  history["link"] = "stocks/"+history.ticker
  history["watchlist"] = "watchlist/52week/"+history.ticker
  history["upvote"] = "upvote/52week/"+history.ticker 
  
  mydata = dict({"data":history.to_dict('records')})
  return jsonify(mydata)



@app.route('/gappers',methods=['GET', 'POST'])
@login_required
def gappers():

  form1 = SearchForm()
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("gappers.html", title = "Gappers", form1 = form1)

  return render_template("gappers.html", title = "Gappers",form1 = form1)

@app.route('/customscanner')
@login_required
def customscanner():
  return redirect("underdevelopment")


@app.route('/forgotpassword')
def forgotpassword():
  return render_template("forgot-password.html")

@app.route('/underdevelopment')

def underdevelopment():
  return render_template("underdevelopment.html")


@app.route('/profile')
@login_required
def profile():
  try:
    token = func.read_from_database("Select token from api_token where user_id ="+ str(current_user.id) +" order by date_created DESC limit 1;", serverSiteUser).iloc[0,0]
  except:
    token = "No Token Found"

  form1 = SearchForm()
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("profile.html", title= "profile" ,form1 = form1, token = token)

  return render_template("profile.html", title= "profile" ,form1 = form1, token = token)

@app.route('/createtoken')
@login_required
def token():
  random_token = str(uuid.uuid4())
  token = ApiToken(token = random_token, user_id = current_user.id)
  db.session.add(token)
  db.session.commit()
  flash('New token created!', 'dark')
  return redirect("https://stockfront.appspot.com"+"/profile")

@app.route('/search')
@login_required
def search():
  return redirect("underdevelopment")

@app.route('/stocks/<stock>', methods = ["GET", "POST"])
@login_required
def stock_overview(stock):

  newsdata= pd.read_json("https://cloud.iexapis.com/stable/stock/"+str(stock)+"/news/last/4?token="+iexKey)
  stockdata = pd.read_json("https://cloud.iexapis.com/stable/stock/"+str(stock)+"/stats?token="+iexKey, typ='series')
  #Get latest data for stock
  latest_data = func.read_from_database("SELECT date, close from dailydata WHERE ticker = '"+ stock + "' ORDER BY date ASC LIMIT 100 ", serverSite)
  #mydata= dict({"latest_data":wl_export_pd.to_dict('records')})

  form1 = SearchForm()
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("stock.html",  stock = stock, dates = json.dumps(list(latest_data.date)), close = list(latest_data.close), form1 = form1, newsdata = newsdata,
                                float = '{:,.0f}'.format(stockdata.float), pe = stockdata.peRatio, marketcap = '{:,.0f}'.format(stockdata.marketcap), beta = round(stockdata.beta,2),
                                week52High = stockdata.week52high, week52low = stockdata.week52low, sma50 =  stockdata.day50MovingAvg, sma200 =  stockdata.day200MovingAvg, companyName = stockdata.companyName)


  return render_template("stock.html", stock = stock, dates = json.dumps(list(latest_data.date)), close = list(latest_data.close), form1 = form1, newsdata = newsdata,
                          float = '{:,.0f}'.format(stockdata.float), pe = stockdata.peRatio, marketcap = '{:,.0f}'.format(stockdata.marketcap), beta = round(stockdata.beta,2),
                          week52High = stockdata.week52high, week52low = stockdata.week52low, sma50 =  stockdata.day50MovingAvg, sma200 =  stockdata.day200MovingAvg, companyName = stockdata.companyName)
  



@app.route('/stocks/<stock>/chart',methods = ["GET", "POST"])
@login_required
def stock_chart(stock):

  form1 = SearchForm()
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("stockchart.html", stock = stock , form1 = form1)
  
  #Show tradingview chart
  return render_template("stockchart.html", stock = stock, form1= form1 )

#Upvoting
@app.route('/upvote/gapper/<stock>')
@login_required
def stock_upvote_gapper(stock):

  #Done.
  upvote = Upvote(ticker = stock, user_id = current_user.id, scanner = "Gapper")
  db.session.add(upvote)
  db.session.commit()
  flash(stock+' was upvoted!', 'dark')
  return redirect("https://stockfront.appspot.com"+"/gappers")

@app.route('/upvote/52week/<stock>')
@login_required
def stock_upvote_52week(stock):

  #Done.
  upvote = Upvote(ticker = stock, user_id = current_user.id, scanner = "52Week")
  db.session.add(upvote)
  db.session.commit()
  flash(stock+' was upvoted!', 'dark')
  return redirect("https://stockfront.appspot.com"+"/week52")


@app.route('/upvote/home/<stock>')
@login_required
def stock_upvote_home(stock):

  upvote = Upvote(ticker = stock, user_id = current_user.id, scanner = "Upvote table")
  db.session.add(upvote)
  db.session.commit()
  flash(stock+' was upvoted!', 'dark')
  return redirect("https://stockfront.appspot.com"+"/home")



#Adding to watchlist
@app.route('/watchlist/gapper/<stock>')
@login_required
def add_watchlist_gapper(stock):

  wl_stock = WatchlistStock(ticker = stock, user_id = current_user.id, scanner = "Gapper")
  db.session.add(wl_stock)
  db.session.commit()
  print("Added", stock, "to watchlist", file=sys.stderr)
  flash(stock+' has been added to your watchlist!', 'dark')
  return redirect("https://stockfront.appspot.com"+"/gappers")


@app.route('/watchlist/52week/<stock>')
@login_required
def add_watchlist_52week(stock):

  wl_stock = WatchlistStock(ticker = stock, user_id = current_user.id, scanner = "52Week")
  db.session.add(wl_stock)
  db.session.commit()
  flash(stock+' has been added to your watchlist!', 'dark')
  return redirect("https://stockfront.appspot.com"+"/week52")

@app.route('/watchlist/own/<stock>')
@login_required
def add_watchlist_own(stock):

  wl_stock = WatchlistStock(ticker = stock, user_id = current_user.id, scanner = "Own")
  db.session.add(wl_stock)
  db.session.commit()
  flash(stock+' has been added to your watchlist!', 'dark')
  return redirect("https://stockfront.appspot.com"+"/home")

@app.route('/watchlist/home/<stock>')
@login_required
def add_watchlist_upvotetable(stock):

  wl_stock = WatchlistStock(ticker = stock, user_id = current_user.id, scanner = "Upvote table")
  db.session.add(wl_stock)
  db.session.commit()
  flash(stock+' has been added to your watchlist!', 'dark')
  return redirect("https://stockfront.appspot.com"+"/home")


@app.route('/AI-Charlie',methods = ['GET','POST'])
@login_required
def charlie():
  form1 = SearchForm()
  charlie_status = "Online!"
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("charlie.html", title= "Charlie" ,form1 = form1, charlie_status = charlie_status)

  return render_template("charlie.html", title= "Charlie" ,form1 = form1, charlie_status= charlie_status)



@app.route('/AI-Delta',methods = ['GET','POST'])
@login_required
def delta():
  form1 = SearchForm()
  delta_status = "Online"
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("delta.html", title= "Delta" ,form1 = form1, delta_status = delta_status)

  return render_template("delta.html", title= "Delta" ,form1 = form1, delta_status= delta_status)


@app.route('/AI-Echo',methods = ['GET','POST'])
@login_required
def echo():
  form1 = SearchForm()
  echo_status = "Online"

  #Creating the data for the bar graph. Resulting df is called active
  active  = func.read_from_database("SELECT * from active_trades_echo", serverSite)
  active["port_weight"] = (active.qty.astype("float64") * active.current_price.astype("float64"))/sum(active.qty.astype("float64") * active.current_price.astype("float64"))
  active.port_weight = round(active.port_weight*100,2)
  active = active.sort_values(by="port_weight", ascending= False)

  max_y = max(active.port_weight.tolist())+5

  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("echo.html", title= "Echo" ,form1 = form1, echo_status = echo_status, active = active, max_y = max_y)

  return render_template("echo.html", title= "Echo" ,form1 = form1, echo_status = echo_status, active = active,max_y = max_y)


#Charlies data 1
@app.route('/charliehistory')
@login_required
def charliehistory():
  history = func.read_from_database("SELECT * from tradehistory order by timestamp DESC limit 20", serverSite)
  history["link"] = "stocks/"+history.Ticker
  
  mydata = dict({"data":history.to_dict('records')})
  return jsonify(mydata)

#Charlies data 2
@app.route('/charlieactive')
@login_required
def charlieactive():
  active = func.read_from_database("SELECT * from active_trades", serverSite)
  active["link"] = "stocks/"+active.ticker
  active.StopPrice = round(active.StopPrice,2)
  active.TargetPrice = round(active.TargetPrice,2)
  
  mydata = dict({"data":active.to_dict('records')})
  return jsonify(mydata)

#Charlies data3 
@app.route('/charliewl')
@login_required
def charliewl():
  wl = func.read_from_database("SELECT * from ma_watchlist", serverSite)#ma
  wl_hd = func.read_from_database("SELECT * from hd_watchlist", serverSite)#hd
  wl = wl.append(wl_hd)
  wl["link"] = "stocks/"+wl.ticker

  try:
    wl.price_difference = round(wl.price_difference,2)
  except:
    pass #if it fails then the df is just empty.

  mydata = dict({"data":wl.to_dict('records')})
  return jsonify(mydata)

#Deltas data1
@app.route('/deltahistory')
@login_required
def deltahistory():
  history = func.read_from_database("SELECT * from tradehistory_delta LIMIT 20", serverSite)
  history["link"] = "stocks/"+history.Ticker
  
  mydata = dict({"data":history.to_dict('records')})
  return jsonify(mydata)

#Deltas data2
@app.route('/deltaactive')
@login_required
def deltaactive():
  active = func.read_from_database("SELECT * from active_trades_delta", serverSite)
  active["link"] = "stocks/"+active.ticker
  active.StopPrice = round(active.StopPrice,2)
  active.TargetPrice = round(active.TargetPrice,2)
  
  mydata = dict({"data":active.to_dict('records')})
  return jsonify(mydata)

#Deltas data3
@app.route('/deltawl')
@login_required
def deltawl():
  wl = func.read_from_database("SELECT * from week_watchlist", serverSite)
  wl["link"] = "stocks/"+wl.ticker
  
  mydata = dict({"data":wl.to_dict('records')})
  return jsonify(mydata)


#Echos data
@app.route('/echoactive')
@login_required
def echoactive():
  active = func.read_from_database("SELECT * from active_trades_echo;", serverSite)
  active["link"] = "stocks/"+active.ticker
  active.unreal_pl = round(active.unreal_pl.astype("float64"),3)
  
  mydata = dict({"data":active.to_dict('records')})
  return jsonify(mydata)


#API

aidata = ["tradehistory", "watchlist", "active_trades"] #The available data
@app.route('/api.v<version>/<ai>/<data>/limit=<limit>&token=<token>')
def baseapi(version,ai,data,limit,token):
  # Setting max limit to 20 
  if int(limit)  > 20:
    limit = str(20) 

  #Checking validity of token
  try:
    token = func.read_from_database("Select 1 from api_token where token = '"+ str(token).replace(" ","")+"';",serverSiteUser).iloc[0,0]
  except:
    token = False

  if token == True:
    if int(version) == 1:
      if str(ai) == "delta" or str(ai) == "charlie":

        #In the database the table names are for example just "tradehistory" for charlie, but for delta they are "tradehistory_delta", so if delta add delta to the end.
        if str(ai) == "delta":
          ai = "_delta"
        else:
          ai = ""

        if data in aidata:
            #Query db accoring to the requested url and return the results
            fetched_data = func.read_from_database("Select * from "+ data +ai+ " limit "+ str(limit) +";", serverSite)
            mydata = dict({"data":fetched_data.to_dict('records')})
            return jsonify(mydata)
        else:
          return "Requested data not supported"
      else:
        return "Ai not found, currently API only supports delta or charlie"
    else:
      return "Version not supported"
  else: 
    return "Access not allowed, token not accepted"



@app.route('/api')
@login_required
def apiroute():

  try:
    token = func.read_from_database("Select token from api_token where user_id ="+ str(current_user.id) +" order by date_created DESC limit 1;", serverSiteUser).iloc[0,0]
  except:
    token = "No Token Found"

  form1 = SearchForm()
  if  form1.validate_on_submit():
      ticker = (form1.search.data).upper()
      if ticker in tickers:
        return redirect('stocks/'+ ticker )
      else:
        flash("No stock with the ticker "+ ticker +" was found", 'dark')
        return render_template("ai-api.html", title= "API" ,form1 = form1, token = token)

  return render_template("ai-api.html", title= "API" ,form1 = form1, token = token)





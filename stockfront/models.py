from stockfront import db, login_manager
from datetime import datetime
import pytz

from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  firstname = db.Column(db.String(20), nullable = False)
  lastname = db.Column(db.String(20), nullable = False)
  email = db.Column(db.String(120), unique = True, nullable = False)
  image_file = db.Column(db.String(20), nullable = False, default = 'default.jpg')
  password = db.Column(db.String(60), nullable = False)
  subscription = db.Column(db.String(50), nullable = False, default = "Free")

  def __repr__(self):
    return "User "+self.firstname+','+self.lastname+', '+ self.email+', '+self.image_file

class Upvote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(6), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default= datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scanner = db.Column(db.String(15))

    def __repr__(self):
        return "Upvote "+self.ticker+','+self.user_id+', '+ self.date_posted+', '+self.scanner



class WatchlistStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(6), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scanner = db.Column(db.String(15))


    def __repr__(self):
        return "Watchlist "+self.ticker+','+self.user_id+', '+ self.id+', '+self.scanner



    
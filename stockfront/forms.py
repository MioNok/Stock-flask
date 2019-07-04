from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from stockfront.models import User
from flask import flash, request
import sys
import pytz


class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_check = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email is not None:
            flash('That email is taken, please choose another one!', 'danger')
            raise ValidationError('That email is taken. Please choose a different one.')
            

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpvoteForm(FlaskForm):
    submit = SubmitField('Upvote')

class SearchForm(FlaskForm):
  search = StringField('search',validators=[DataRequired()])
  submit = SubmitField('Search')

class WLForm(FlaskForm):
  ticker = StringField('ticker',validators=[DataRequired()])
  submit = SubmitField('Add')
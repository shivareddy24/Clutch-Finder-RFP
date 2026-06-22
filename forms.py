from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField,
                     SelectField, TextAreaField, HiddenField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional


class RegistrationForm(FlaskForm):
    username         = StringField('Username',
                                   validators=[DataRequired(), Length(min=2, max=20)])
    email            = StringField('Email',    validators=[DataRequired(), Email()])
    password         = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit           = SubmitField('Create Account')


class LoginForm(FlaskForm):
    email    = StringField('Email',    validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Login')


class PostForm(FlaskForm):
    title   = StringField('Title',   validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit  = SubmitField('Post')


class PlayerForm(FlaskForm):
    name = StringField('Player Name',
                       validators=[DataRequired(), Length(min=2, max=100)])

    category = SelectField('Category', choices=[
        ('batsman', 'Batsman'),
        ('allrounder', 'All-Rounder'),
        ('bowler', 'Bowler'),
    ], validators=[DataRequired()])

    runs    = StringField('Runs', validators=[Optional(), Length(max=10)])
    avg     = StringField('Batting Average', validators=[Optional(), Length(max=10)])
    hs      = StringField('Highest Score', validators=[Optional(), Length(max=10)])

    wickets = StringField('Wickets', validators=[Optional(), Length(max=10)])
    eco     = StringField('Economy Rate', validators=[Optional(), Length(max=10)])
    best    = StringField('Best Figures', validators=[Optional(), Length(max=10)])

    image = FileField('Player Photo',
                      validators=[Optional(),
                                  FileAllowed(['jpg','jpeg','png'], 'Images only')])

    # 🔥 ADD THIS
    video = FileField('Player Video',
                      validators=[Optional(),
                                  FileAllowed(['mp4','webm','mov','avi'], 'Video only')])

    submit = SubmitField('Save Player')

class VideoForm(FlaskForm):
    title       = StringField('Video Title',
                              validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField('Description',
                                validators=[Optional(), Length(max=500)])
    video       = FileField('Highlight Clip',
                            validators=[DataRequired(),
                                        FileAllowed(['mp4','webm','mov','avi'],
                                                    'Video files only')])
    submit      = SubmitField('Upload Clip')


class RatingForm(FlaskForm):
    value  = HiddenField('Rating', validators=[DataRequired()])
    submit = SubmitField('Rate')
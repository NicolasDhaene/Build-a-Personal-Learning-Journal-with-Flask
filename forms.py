from flask_wtf import FlaskForm
from wtforms import (IntegerField, TextAreaField, StringField,
                     DateTimeField, PasswordField)
from wtforms.validators import DataRequired, Email, EqualTo


class EntryForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    date = DateTimeField("Date (dd/mm/yyyy)",
                         validators=[DataRequired()], format='%d/%m/%Y')
    time_spent = IntegerField("Duration in minutes (integer only)",
                              validators=[DataRequired()])
    material = TextAreaField("What i have Learned",
                             validators=[DataRequired()])
    resource = TextAreaField("Resources", validators=[DataRequired()])
    tagfield = StringField("Tag (Optional - Separate each tag with a comma)")


class RegistrationForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password1 = PasswordField("Password",
                              validators=[DataRequired(),
                                          EqualTo("password2")])
    password2 = PasswordField("Confirm Password", validators=[DataRequired()])


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])

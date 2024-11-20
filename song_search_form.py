from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired

# Form class for song searching
class SongSearchForm(FlaskForm):
    artistName = StringField("Enter the name of the artist", validators=[DataRequired()])
    submit = SubmitField("Submit")
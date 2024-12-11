from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerRangeField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, NumberRange

"""
Form class for searching recommended songs. This class is needed to implement a custom WTForms for searching
a song. 
"""
class RecommendSongs(FlaskForm):
    nameOfGame = SelectField("Select the game: ", choices = [], validators=[DataRequired()]) # Drop down menu
    numSongs = IntegerRangeField('Number of Songs', [NumberRange(min = 1, max = 5)]) # Slider for selecting the number of songs
    submit = SubmitField("Submit")


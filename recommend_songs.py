from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerRangeField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, NumberRange

# Form class for song searching
class RecommendSongs(FlaskForm):
    nameOfGame = StringField("Enter the name of a game", validators=[DataRequired()])
    numSongs = IntegerRangeField('Number of Songs', [NumberRange(min = 1, max = 100)])
    submit = SubmitField("Submit")


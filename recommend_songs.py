from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired

# Form class for song searching
class RecommendSongs(FlaskForm):
    nameOfGame = StringField("Enter the name of a game", validators=[DataRequired()])
    submit = SubmitField("Submit")
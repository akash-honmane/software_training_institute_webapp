from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class EnquiryForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(min=1, max=128)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=1, max=1024)])
    submit = SubmitField('Submit Inquiry')


class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=64)])
    contact = StringField('Contact', validators=[DataRequired(), Length(min=1, max=20)])
    bio = TextAreaField('Bio', validators=[Length(max=1024)])
    profile_picture = StringField('Profile Picture URL', validators=[Length(max=120)])
    submit = SubmitField('Update Profile')


class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired(), Length(min=1, max=128)])
    description = TextAreaField('Course Description', validators=[DataRequired(), Length(min=1, max=1024)])
    instructor = StringField('Instructor', validators=[DataRequired(), Length(min=1, max=64)])
    submit = SubmitField('Add Course')

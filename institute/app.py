from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, User, Enquiry, Course, ContactMessage
from forms import ProfileForm, EnquiryForm
from sqlalchemy.exc import IntegrityError
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import random
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('application.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Twilio configuration
TWILIO_ACCOUNT_SID = 'AC1527cf2a85e4f1ae82d31ba60e0e08eb'
TWILIO_AUTH_TOKEN = '796655dc50862198612f9ce8c78e06dc'
TWILIO_PHONE_NUMBER = '+12253517114'

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'py.my.testing@gmail.com'
app.config['MAIL_PASSWORD'] = 'liud rnbd sqhm shtu'
app.config['MAIL_DEFAULT_SENDER'] = ('Future Talent Academy', 'py.my.testing@gmail.com')

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

logging.basicConfig(level=logging.DEBUG)


def send_otp_email(email):
    otp = str(random.randint(1000, 9999))
    session['email_otp'] = otp
    msg = Message('Your OTP', recipients=[email])
    msg.body = f"Your OTP is {otp}"
    try:
        mail.send(msg)
        logging.info(f'OTP email sent to {email}')
    except Exception as e:
        logging.error(f'Error sending OTP email: {e}')


def send_otp_contact(contact):
    try:
        otp = str(random.randint(1000, 9999))
        session['contact_otp'] = otp
        message = f"Your OTP is {otp}"
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=contact
        )
        logging.info(f'OTP SMS sent to {contact}')
    except Exception as e:
        logging.error(f'Error sending OTP SMS: {e}')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('You must be logged in to view the dashboard.', 'danger')
        return redirect(url_for('login'))

    form = EnquiryForm()
    if request.method == 'POST' and form.validate_on_submit():
        user_id = session['user_id']
        subject = form.subject.data
        message = form.message.data
        enquiry = Enquiry(user_id=user_id, subject=subject, message=message)

        try:
            db.session.add(enquiry)
            db.session.commit()
            flash('Your enquiry has been submitted.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('There was an error with your submission. Please try again.', 'danger')
            logger.error(f'Error submitting enquiry: {str(e)}')

    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user, form=form)


@app.route('/', methods=['GET', 'POST'])
def home():
    form = EnquiryForm()
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    if request.method == 'POST':
        if form.validate_on_submit():
            # Process the form data
            subject = form.subject.data
            message = form.message.data
            # Add your logic to handle the enquiry form submission
            flash('Your enquiry has been submitted successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('There was an error with your submission. Please try again.', 'danger')

    return render_template('home.html', user=user, form=form)


@app.route('/enquire/<int:course_id>', methods=['GET', 'POST'])
def enquire(course_id):
    course = Course.query.get_or_404(course_id)
    form = EnquiryForm()
    if form.validate_on_submit():
        user_id = session.get('user_id')
        if not user_id:
            flash('You must be logged in to submit an enquiry.', 'danger')
            return redirect(url_for('login'))
        subject = form.subject.data
        message = form.message.data
        enquiry = Enquiry(user_id=user_id, course_id=course.id, subject=subject, message=message)
        try:
            db.session.add(enquiry)
            db.session.commit()
            flash('Your enquiry has been submitted.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('There was an error with your submission. Please try again.', 'danger')
            logger.error(f'Error submitting enquiry: {str(e)}')
    form.message.data = f"I am interested in the {course.name} course and would like more information."
    return render_template('enquire.html', course=course, form=form)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('You must be logged in to view your profile.', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    form = ProfileForm(obj=user)

    if form.validate_on_submit():
        user.name = form.name.data
        user.contact = form.contact.data
        user.bio = form.bio.data
        user.profile_picture = form.profile_picture.data
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USE_SSL'] = False
        app.config['MAIL_USERNAME'] = 'py.my.testing@gmail.com'
        app.config['MAIL_PASSWORD'] = 'liud rnbd sqhm shtu'
        app.config['MAIL_DEFAULT_SENDER'] = ('Akash', 'py.my.testing@gmail.com')
        return redirect(url_for('profile'))

    return render_template('profile.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists. Please use a different email.', 'warning')
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, contact=contact)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()

            # Generate OTPs and store them in session (before sending)
            otp = str(random.randint(1000, 9999))
            session['email_otp'] = otp
            contact_otp = str(random.randint(1000, 9999))
            session['contact_otp'] = contact_otp

            # Display flash message before sending OTPs
            flash('OTPs sent to your email and contact number. Please verify.', 'success')

            # Send OTPs via email and SMS
            send_otp_email(email)
            send_otp_contact(contact)
            session['new_user_id'] = new_user.id  # Store the new user ID in the session
            return redirect(url_for('verify_otp'))
        except IntegrityError:
            db.session.rollback()
            flash('Email address already exists. Please use a different email.', 'warning')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            logger.error(f'Error registering user: {str(e)}')

    return render_template('register.html')


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        email_otp = request.form['email_otp']
        contact_otp = request.form['contact_otp']
        if email_otp == session.get('email_otp') and contact_otp == session.get('contact_otp'):
            session.pop('email_otp', None)
            session.pop('contact_otp', None)
            new_user_id = session.pop('new_user_id', None)
            if new_user_id:
                user = User.query.get(new_user_id)
                session['user_id'] = user.id
                flash('OTPs verified successfully! Registration complete.', 'success')
                return redirect(url_for('home'))
            flash('OTPs verified but user registration not found.', 'warning')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTPs. Please try again.', 'danger')
    return render_template('verify_otp.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out!')
    return redirect(url_for('home'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(user.email, salt='password-reset-salt')
            print(f"Generated token: {token}")  # Debug print
            reset_url = url_for('reset_password', token=token, _external=True)
            print(f"Reset URL: {reset_url}")  # Debug print
            html = render_template('reset_password_email.html', reset_url=reset_url)
            msg = Message('Password Reset Request', recipients=[email])
            msg.html = html
            try:
                mail.send(msg)
                flash('A password reset link has been sent to your email.', 'info')
            except Exception as e:
                flash(f'An error occurred while sending the email: {e}', 'danger')
        else:
            flash('Email address not found.', 'warning')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
        print(f"Token is valid. Email: {email}")  # Debug print
    except Exception as e:
        print(f"Token error: {e}")  # Debug print
        flash('The password reset link is invalid or has expired.', 'warning')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if len(password) < 8:
            flash('Password must be at least 8 characters.')
            return redirect(url_for('reset_password', token=token))

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('reset_password', token=token))

        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Your password has been reset!', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', token=token)


@app.route('/contact', methods=['POST'])
def save_message():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    # Create a new ContactMessage object
    msg = ContactMessage(name=name, email=email, message=message)
    # Add the object to the session
    db.session.add(msg)
    # Commit the changes
    db.session.commit()
    # Redirect to a success page
    return redirect(url_for('success'))


@app.route('/success')
def success():
    return 'Message sent successfully!'


@app.route('/course_programs')
def course_programs():
    popular_courses = Course.query.filter_by(popular=True).all()
    all_courses = Course.query.all()
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('course_programs.html', popular_courses=popular_courses, all_courses=all_courses, user=user)


@app.route('/about_us')
def about_us():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        user = None
    return render_template('about_us.html', user=user)


@app.route('/contact_us')
def contact_us():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        user = None
    return render_template('contact_us.html',user=user)


@app.route('/gallery')
def gallery():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    else:
        user = None
    return render_template('gallery.html')


def create_tables():
    db.create_all()


if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)

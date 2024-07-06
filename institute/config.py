import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/institutedb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_USERNAME = 'py.my.testing@gmail.com'
    MAIL_PASSWORD = 'liud rnbd sqhm shtu'


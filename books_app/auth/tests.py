import os
from unittest import TestCase

from datetime import date
 
from books_app.extensions import app, db, bcrypt
from books_app.models import Book, Author, User, Audience

"""
Run these tests with the command:
python -m unittest books_app.main.tests
"""

#################################################
# Setup
#################################################

def create_books():
    a1 = Author(name='Harper Lee')
    b1 = Book(
        title='To Kill a Mockingbird',
        publish_date=date(1960, 7, 11),
        author=a1
    )
    db.session.add(b1)

    a2 = Author(name='Sylvia Plath')
    b2 = Book(title='The Bell Jar', author=a2)
    db.session.add(b2)
    db.session.commit()

def create_user():
    password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
    user = User(username='me1', password=password_hash)
    db.session.add(user)
    db.session.commit()

#################################################
# Tests
#################################################

class AuthTests(TestCase):
    """Tests for authentication (login & signup)."""
 
    def setUp(self):
        """Executed prior to each test."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    def test_signup(self):
        response = self.app.post('/signup', data={
            'username': 'new_user',
            'password': 'password'
        }, follow_redirects=True)
        user = User.query.filter_by(username='new_user').first()
        self.assertIsNotNone(user)

    def test_signup_existing_user(self):
        create_user()
        response = self.app.post('/signup', data={
            'username': 'me1',
            'password': 'password'
        }, follow_redirects=True)
        self.assertIn(b'Username already in use', response.data)

    def test_login_correct_password(self):
        create_user()
        self.app.post('/login', data={
            'username': 'me1',
            'password': 'password'
        }, follow_redirects=True)
        home_response = self.app.get('/')
        self.assertNotIn(b'login', home_response.data)

    def test_login_nonexistent_user(self):
        response = self.app.post('/login', data={
            'username': 'nonexistent',
            'password': 'password'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)

    def test_login_incorrect_password(self):
        create_user()
        response = self.app.post('/login', data={
            'username': 'me1',
            'password': 'wrong_password'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)

    def test_logout(self):
        create_user()
        self.app.post('/login', data={
            'username': 'me1',
            'password': 'password'
        }, follow_redirects=True)
        self.app.get('/logout', follow_redirects=True)
        home_response = self.app.get('/')
        self.assertIn(b'login', home_response.data)

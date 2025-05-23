import os
import unittest
import app

from datetime import date
from books_app.extensions import app, db, bcrypt
from books_app.models import Book, Author, User, Audience, Genre

"""
Run these tests with the command:
python -m unittest books_app.main.tests
"""

#################################################
# Setup
#################################################

def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

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
    # Creates a user with username 'me1' and password of 'password'
    password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
    user = User(username='me1', password=password_hash)
    db.session.add(user)
    db.session.commit()

#################################################
# Tests
#################################################

class MainTests(unittest.TestCase):
 
    def setUp(self):
        """Executed prior to each test."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.drop_all()
        db.create_all()
 
    def test_homepage_logged_out(self):
        """Test that the books show up on the homepage."""
        # Set up
        create_books()
        create_user()

        # Make a GET request
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check that page contains all of the things we expect
        response_text = response.get_data(as_text=True)
        self.assertIn('To Kill a Mockingbird', response_text)
        self.assertIn('The Bell Jar', response_text)
        self.assertIn('me1', response_text)
        self.assertIn('Log In', response_text)
        self.assertIn('Sign Up', response_text)

        # Check that the page doesn't contain things we don't expect
        # (these should be shown only to logged in users)
        self.assertNotIn('Create Book', response_text)
        self.assertNotIn('Create Author', response_text)
        self.assertNotIn('Create Genre', response_text)
 
    def test_homepage_logged_in(self):
        """Test that the books show up on the homepage."""
        # Set up
        create_books()
        create_user()
        login(self.app, 'me1', 'password')

        # Make a GET request
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check that page contains all of the things we expect
        response_text = response.get_data(as_text=True)
        self.assertIn('To Kill a Mockingbird', response_text)
        self.assertIn('The Bell Jar', response_text)
        self.assertIn('me1', response_text)
        self.assertIn('Create Book', response_text)
        self.assertIn('Create Author', response_text)
        self.assertIn('Create Genre', response_text)

        # Check that the page doesn't contain things we don't expect
        # (these should be shown only to logged out users)
        self.assertNotIn('Log In', response_text)
        self.assertNotIn('Sign Up', response_text)

    def test_book_detail_logged_out(self):
        """Test that the book appears on its detail page."""
        # Create books, authors, user
        create_books()
        create_user()

        # Make a GET request to the URL /book/1
        response = self.app.get('/book/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check that the response contains the book's title, publish date,
        # and author's name
        response_text = response.get_data(as_text=True)
        self.assertIn("<h1>To Kill a Mockingbird</h1>", response_text)
        self.assertIn("Harper Lee", response_text)
        self.assertIn("July 11, 1960", response_text)  # Format may vary, adjust as needed

        # Check that the response does NOT contain the 'Favorite' button
        self.assertNotIn("Favorite This Book", response_text)

    def test_book_detail_logged_in(self):
        """Test that the book appears on its detail page."""
        # Create books, authors, user, & log in
        create_books()
        create_user()
        login(self.app, 'me1', 'password')

        # Make a GET request to the URL /book/1
        response = self.app.get('/book/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Check that the response contains the book's title, publish date,
        # and author's name
        response_text = response.get_data(as_text=True)
        self.assertIn("<h1>To Kill a Mockingbird</h1>", response_text)
        self.assertIn("Harper Lee", response_text)
        self.assertIn("July 11, 1960", response_text)  # Format may vary, adjust as needed

        # Check that the response contains the 'Favorite' button
        self.assertIn("Favorite This Book", response_text)

    def test_update_book(self):
        """Test updating a book."""
        # Set up
        create_books()
        create_user()
        login(self.app, 'me1', 'password')

        # Make POST request with data
        post_data = {
            'title': 'Tequila Mockingbird',
            'publish_date': '1960-07-12',
            'author': 1,
            'audience': 'CHILDREN',
            'genres': []
        }
        self.app.post('/book/1', data=post_data)
        
        # Make sure the book was updated as we'd expect
        book = Book.query.get(1)
        self.assertEqual(book.title, 'Tequila Mockingbird')
        self.assertEqual(book.publish_date, date(1960, 7, 12))
        self.assertEqual(book.audience, Audience.CHILDREN)

    def test_create_book(self):
        """Test creating a book."""
        # Set up
        create_books()
        create_user()
        login(self.app, 'me1', 'password')

        # Make POST request with data
        post_data = {
            'title': 'Go Set a Watchman',
            'publish_date': '2015-07-14',
            'author': 1,
            'audience': 'ADULT',
            'genres': []
        }
        self.app.post('/create_book', data=post_data)

        # Make sure book was updated as we'd expect
        created_book = Book.query.filter_by(title='Go Set a Watchman').one()
        self.assertIsNotNone(created_book)
        self.assertEqual(created_book.author.name, 'Harper Lee')

    def test_create_book_logged_out(self):
        """
        Test that the user is redirected when trying to access the create book 
        route if not logged in.
        """
        # Set up
        create_books()
        create_user()

        # Make GET request
        response = self.app.get('/create_book')

        # Make sure that the user was redirecte to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login?next=%2Fcreate_book', response.location)

    def test_create_author(self):
        """Test creating an author."""
        # Create a user & login
        create_user()
        login(self.app, 'me1', 'password')

        # Make a POST request to the /create_author route
        post_data = {
            'name': 'J.K. Rowling',
            'biography': 'British author best known for the Harry Potter series'
        }
        response = self.app.post('/create_author', data=post_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify that the author was updated in the database
        created_author = Author.query.filter_by(name='J.K. Rowling').one()
        self.assertIsNotNone(created_author)
        self.assertEqual(created_author.name, 'J.K. Rowling')
        self.assertEqual(created_author.biography, 'British author best known for the Harry Potter series')

    def test_create_genre(self):
        """Test creating a genre."""
        # Create a user & login
        create_user()
        login(self.app, 'me1', 'password')

        # Make a POST request to the /create_genre route
        post_data = {
            'name': 'Fantasy'
        }
        response = self.app.post('/create_genre', data=post_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify that the genre was updated in the database
        created_genre = Genre.query.filter_by(name='Fantasy').one()
        self.assertIsNotNone(created_genre)
        self.assertEqual(created_genre.name, 'Fantasy')

    def test_profile_page(self):
        """Test the user profile page."""
        # Create user
        create_user()
        
        # Make a GET request to the /profile/me1 route
        response = self.app.get('/profile/me1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify that the response shows the appropriate user info
        response_text = response.get_data(as_text=True)
        self.assertIn('me1', response_text)
        self.assertIn('Profile', response_text)
        # You may want to check for more specific user profile information

    def test_favorite_book(self):
        """Test favoriting a book."""
        # Login as the user me1
        create_books()
        create_user()
        login(self.app, 'me1', 'password')

        # Make a POST request to the /favorite/1 route
        response = self.app.post('/favorite/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify that the book with id 1 was added to the user's favorites
        user = User.query.filter_by(username='me1').one()
        self.assertIn(Book.query.get(1), user.favorite_books)

    def test_unfavorite_book(self):
        """Test unfavoriting a book."""
        # Login as the user me1, and add book with id 1 to me1's favorites
        create_books()
        create_user()
        user = User.query.filter_by(username='me1').one()
        book = Book.query.get(1)
        user.favorite_books.append(book)
        db.session.commit()
        
        # Confirm the book is in the user's favorites
        self.assertIn(book, user.favorite_books)
        
        # Login
        login(self.app, 'me1', 'password')

        # Make a POST request to the /unfavorite/1 route
        response = self.app.post('/unfavorite/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify that the book with id 1 was removed from the user's favorites
        user = User.query.filter_by(username='me1').one()
        self.assertNotIn(Book.query.get(1), user.favorite_books)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    reviews = db.relationship('Review', backref='author', lazy=True)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(200), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=True)
    genre = db.Column(db.String(200), nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    cover_image_url = db.Column(db.String(500), nullable=True)
    reviews = db.relationship('Review', backref='book', lazy=True)
    description = db.Column(db.Text, nullable=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

def save_book_to_database(book_data):
    google_id = book_data['id']
    title = book_data['volumeInfo'].get('title')
    authors = ', '.join(book_data['volumeInfo'].get('authors', []))
    genre = ', '.join(book_data['volumeInfo'].get('categories', []))
    published_date = book_data['volumeInfo'].get('publishedDate')
    cover_image_url = book_data['volumeInfo'].get('imageLinks', {}).get('thumbnail')
    description = book_data['volumeInfo'].get('description', '')

    if published_date:
        try:
            published_date = datetime.strptime(published_date, '%Y-%m-%d').date()
        except ValueError:
            try:
                published_date = datetime.strptime(published_date, '%Y-%m').date()
            except ValueError:
                published_date = None

    existing_book = Book.query.filter_by(google_id=google_id).first()
    if not existing_book:
        new_book = Book(
            google_id=google_id,
            title=title,
            author=authors,
            genre=genre,
            publication_date=published_date,
            cover_image_url=cover_image_url,
            description=description
        )
        db.session.add(new_book)
        db.session.commit()






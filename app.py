from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Book, Review, save_book_to_database
from forms import RegistrationForm, LoginForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import requests, random
from flask_migrate import Migrate

from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.app_context().push()
app.config['SECRET_KEY'] = 'your_secret_key'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///capstone_db'


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'gaganbastola04@outlook.com'
app.config['MAIL_PASSWORD'] = 'Harrisburg123$'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'gaganbastola04@outlook.com'
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db.init_app(app)
migrate = Migrate(app, db)

def send_email(to, subject, template):
    msg = Message(subject, recipients=[to])
    msg.html = template
    mail.send(msg)

def get_random_book_recommendation():
    books = Book.query.all()
    if books:
        return random.choice(books)
    return None

def send_weekly_email():
    users = User.query.all()
    book = get_random_book_recommendation()
    if book and users:
        for user in users:
            email_content = render_template(
                'book_recommendation.html', 
                book_title=book.title, 
                book_author=book.author,
                book_description=book.description,
                book_cover_image_url=book.cover_image_url
            )
            send_email(user.email, 'Here is the list of our book recommendation', email_content)

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=send_weekly_email,
    trigger=IntervalTrigger(weeks=1),
    id='send_weekly_email_jon',
    name='Send weekly email to all users',
    replace_existing=True)

@app.route('/trigger-emails', methods=['GET'])
def trigger_emails():
    send_weekly_email()
    return "Emails triggered!"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form.get('query')
        genre = request.form.get('genre').lower()
        return redirect(url_for('search', query=query, genre=genre))

    books = fetch_featured_books()
    return render_template('index.html', books=books)

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('query', '')
    base_url = 'https://www.googleapis.com/books/v1/volumes?'
    api_url = f'{base_url}q={query}&maxResults=5'
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        books = data.get('items', [])
        return jsonify([{'title': book['volumeInfo']['title']} for book in books])
    return jsonify([])

def fetch_featured_books():
    base_url = 'https://www.googleapis.com/books/v1/volumes?'
    api_url = f'{base_url}q=subject:fiction&orderBy=relevance&maxResults=12'
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        books = data.get('items', [])
        return books
    return []

@app.route('/profile')
@login_required
def profile():
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', reviews=reviews)

@app.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        flash('You do not have permission to delete this review.', 'danger')
        return redirect(url_for('profile'))
    
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted!', 'success')
    return redirect(url_for('profile'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if len(form.password.data) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(form.password.data, method='sha256')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.username_or_email.data) | (User.email == form.username_or_email.data)).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        flash('Login Unsuccessful. Please check your credentials.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out!','success')
    return redirect(url_for('index'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    books = []
    query = request.args.get('query', '')
    genre = request.args.get('genre', '').lower()
    page = request.args.get('page', 1, type=int)
    startIndex = (page - 1) * 40

    if request.method == 'POST':
        query = request.form.get('query')
        genre = request.form.get('genre').lower()

    books = search_books(query, genre, startIndex)
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if len(books) == 40 else None

    return render_template('search.html', books=books, page=page, query=query, genre=genre, prev_page=prev_page, next_page=next_page)

def search_books(query, genre, startIndex=0):
    base_url = 'https://www.googleapis.com/books/v1/volumes?'
    api_url = f'{base_url}q={query}'

    if genre:
        api_url += f"+subject:{genre}"

    api_url += f'&startIndex={startIndex}&maxResults=40'
    
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        books = data.get('items', [])
        for book_data in books:
            existing_book = Book.query.filter_by(google_id=book_data['id']).first()
            if not existing_book:
                save_book_to_database(book_data)
        return books
    return []


API_KEY = Config.MOVIE_API_KEY
READ_ACCESS_TOKEN = Config.MOVIE_READ_ACCESS_TOKEN


def fetch_movie_by_title(title):
    headers = {
        'Authorization' : f'Bearer {READ_ACCESS_TOKEN}'
    }
    params = {
        'api_key': API_KEY,
        'query': title,
    }
    response = requests.get('https://api.themoviedb.org/3/search/movie', headers=headers, params=params)

    if response.status_code == 200:
        return response.json()['results']
    return None

@app.route('/book/<book_id>', methods=['GET', 'POST'])
@login_required
def book_details(book_id):
    book = Book.query.filter_by(google_id=book_id).first()
    if not book:
        flash('Book not found!', 'danger')
        return redirect(url_for('index'))

    movie_data = fetch_movie_by_title(book.title)

    book_title = book.title
    book_description_gpt = generate_book_description(book_title)

    if request.method == 'POST':
        review_content = request.form.get('review_content')
        rating = request.form.get('rating')
        user_id = current_user.id
        review = Review(content=review_content, rating=rating, user_id=user_id, book_id=book.id)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been submitted!', 'success')
        return redirect(url_for('book_details', book_id=book_id))
    
    book_description = book.description if book.description else "No description available"
    return render_template('book_details.html', book=book, movie_data=movie_data, book_description=book_description, book_description_gpt=book_description_gpt)

def generate_book_description(book_title):
    openai.api_key = Config.OPENAI_API_KEY
    prompt = f'Describe the essence or main idea of the book titled "{book_title} in an entertaining way"'
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=4000,
        n=1,
        stop=None,
        temperature=0.7
    )

    if response and response.choices:
        return response.choices[0].text.strip()
    return "No description available."
    
if __name__ == '__main__':
    app.run(debug=True)

import os

class Config:
    SECRET_KEY = 'your_secret_key'
    # SQLALCHEMY_DATABASE_URI = 'postgresql:///capstone_db'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'your_fallback_database_uri').replace("://", "ql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USERNAME = 'gaganbastola04@outlook.com'
    MAIL_PASSWORD = 'Harrisburg123$'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_DEFAULT_SENDER = 'gaganbastola04@outlook.com'
    
    OPENAI_API_KEY = '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'
    
    MOVIE_API_KEY = 'b1da920267f20e50aa9f4f2bd6ea4ead'
    MOVIE_READ_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiMWRhOTIwMjY3ZjIwZTUwYWE5ZjRmMmJkNmVhNGVhZCIsInN1YiI6IjY1MWFlYjc5OTNiZDY5MDExYjhlZGVhOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.kO6RpsrkiLfd3GnC4BwVUpi6ZJqA4oq3yf6J_h_xHxI'

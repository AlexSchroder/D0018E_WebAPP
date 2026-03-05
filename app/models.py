from . import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='Customer')
    reviews = db.relationship('Review', backref='author', lazy=True)
    
    # RELATIONSHIP: One User has Many Orders
    # 'backref' creates a fake column 'user' in the Order table so we can say order.user
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')
    reviews = db.relationship('Review', backref='product', lazy=True, cascade="all, delete-orphan")

    # RELATIONSHIP: This allows us to see how many times a product has been ordered
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    @property
    def average_rating(self):
        # If there are no reviews, return 0
        if not self.reviews:
            return 0.0
        
        #Calculate sum of all ratings divided by the number of reviews
        total_stars = sum(review.rating for review in self.reviews)
        avg = total_stars / len(self.reviews)
        
        # Return it rounded to 1 decimal 
        return round(avg, 1)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Numeric(10, 2), default=0.00)
    status = db.Column(db.String(20), default='Pending') # e.g. Pending, Paid, Shipped
    
    # FOREIGN KEY: Links this order to a specific user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # RELATIONSHIP: One Order has Many OrderItems
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False) #Stores price at time of buying
    
    # FOREIGN KEYS
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys to show who wrote it and what product it concerns
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # The review
    rating = db.Column(db.Integer, nullable=False) #Should be a vlaue between 1-5
    comment = db.Column(db.Text, nullable=True)    #Should be able to be empty, if the opnly what to leave a star reviw
    
    #Timestamnp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
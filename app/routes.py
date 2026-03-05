from flask import Blueprint, render_template, abort, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from decimal import Decimal, InvalidOperation
from flask import request
from . import db
from .models import Product, User, Order, OrderItem, Review
from .seed import seed_products
from flask import session, flash


bp = Blueprint("main", __name__)



@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="Email already registered")
            
        # Create new user
        new_user = User(email=email, role="Customer") # Default role is Customer
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log them in immediately 
        session["user_id"] = new_user.id
        session["role"] = new_user.role
        
        return redirect("/products")
        
    return render_template("register.html")

# ---------- helpers ----------
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


def is_admin():
    return session.get("role") == "admin"


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user.role != "admin":
            return redirect(url_for("main.login_form"))
        return view(*args, **kwargs)
    return wrapped


@bp.app_context_processor
def inject_user():
    # lets templates use: current_user, is_admin
    return {"current_user": current_user(), "is_admin": is_admin()}


# ---------- public ----------
@bp.get("/")
def home():
    return redirect("/products")


@bp.get("/health/db")
def health_db():
    db.session.execute(db.text("SELECT 1"))
    return {"db": "ok"}



@bp.get("/seed")
def seed():
    seed_products()
    return {"seed": "done"}




@bp.get("/seed/users")
def seed_users():

    admin_email = "admin@gymshop.local"

    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        return {"seed_users": "already exists"}

    admin = User(
        email=admin_email,
        password_hash=generate_password_hash("admin123"),
        role="admin",
    )
    db.session.add(admin)
    db.session.commit()

    return {"seed_users": "created admin", "email": admin_email, "password": "admin123"}


@bp.get("/products")
def products_list():
    
    selected_category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "").strip()

    
    q = Product.query

    
    if selected_category and selected_category != "all":
        q = q.filter(Product.category == selected_category)

    
    if sort == "price_asc":
        q = q.order_by(Product.price.asc())
    elif sort == "price_desc":
        q = q.order_by(Product.price.desc())
    elif sort == "name_asc":
        q = q.order_by(Product.name.asc())
    else:
        q = q.order_by(Product.id.asc())

    products = q.all()

   
    categories = (
        db.session.query(Product.category)
        .distinct()
        .all()
    )
    categories = sorted([c[0] for c in categories if c[0]])

    return render_template(
        "products.html",
        products=products,
        categories=categories,
        selected_category=selected_category or "all",
        sort=sort or "default",
    )



@bp.get("/products/<int:product_id>")
def product_detail(product_id: int):
    product = Product.query.get(product_id)
    if not product:
        abort(404)
    return render_template("product_detail.html", product=product)



@bp.get("/login")
def login_form():
    return render_template("login.html")


@bp.post("/login")
def login_submit():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render_template("login.html", error="Wrong email or password")

    session["user_id"] = user.id
    session["role"] = user.role
    if user.role.lower() == 'admin':
        return redirect("/admin")
    else:
        # Customers go to the shop
        return redirect("/products")


@bp.get("/logout")
def logout():
    session.clear()
    return redirect("/products")


# ---------- admin ----------
@bp.get("/admin")
@admin_required
def admin_home():
    return render_template("admin.html")


@bp.get("/admin/products")
@admin_required
def admin_products():
    products = Product.query.order_by(Product.id.asc()).all()
    return render_template("admin_products.html", products=products)


@bp.get("/admin/products/new")
@admin_required
def admin_products_new_form():
    return render_template("admin_product_form.html", product=None)


@bp.post("/admin/products/new")
@admin_required
def admin_products_new_submit():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip() or None
    description = request.form.get("description", "").strip() or None

    price_raw = request.form.get("price", "").strip()
    stock_raw = request.form.get("stock", "").strip()
    image_file = request.form.get("image_file", "").strip() or "default.jpg"

    if not name:
        return render_template("admin_product_form.html", product=None, error="Name is required")

    try:
        price = Decimal(price_raw)
    except (InvalidOperation, ValueError):
        return render_template("admin_product_form.html", product=None, error="Price must be a number")

    try:
        stock = int(stock_raw)
    except ValueError:
        return render_template("admin_product_form.html", product=None, error="Stock must be an integer")

    p = Product(name=name, category=category, description=description, price=price, stock=stock, image_file=image_file)
    db.session.add(p)
    db.session.commit()
    return redirect("/admin/products")


@bp.get("/admin/products/<int:product_id>/edit")
@admin_required
def admin_products_edit_form(product_id: int):
    product = Product.query.get(product_id)
    if not product:
        abort(404)
    return render_template("admin_product_form.html", product=product)


@bp.post("/admin/products/<int:product_id>/delete")
@admin_required
def admin_products_delete(product_id: int):
    product = Product.query.get(product_id)
    if not product:
        abort(404)

    db.session.delete(product)
    db.session.commit()
    return redirect("/admin/products")


@bp.post("/admin/products/<int:product_id>/edit")
@admin_required
def admin_products_edit_submit(product_id: int):
    product = Product.query.get(product_id)
    if not product:
        abort(404)

    product.name = request.form.get("name", "").strip()
    product.category = request.form.get("category", "").strip() or None
    product.description = request.form.get("description", "").strip() or None
    product.image_file = request.form.get("image_file", "").strip() or "default.jpg"

    price_raw = request.form.get("price", "").strip()
    stock_raw = request.form.get("stock", "").strip()

    try:
        product.price = Decimal(price_raw)
    except (InvalidOperation, ValueError):
        return render_template("admin_product_form.html", product=product, error="Price must be a number")

    try:
        product.stock = int(stock_raw)
    except ValueError:
        return render_template("admin_product_form.html", product=product, error="Stock must be an integer")

    db.session.commit()
    return redirect("/admin/products")


# ---------- CART ----------
@bp.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    #  Get the current cart from the session (or create an empty one)
    # We use .get() to avoid errors if 'cart' doesn't exist yet
    cart = session.get('cart', {})

    #Check if product is already in cart
    # We convert product_id to string because JSON keys are always strings
    str_id = str(product_id)
    
    if str_id in cart:
        cart[str_id] += 1 # Increment quantity
    else:
        cart[str_id] = 1  # Add new item

    #  Save the cart back to the session
    session['cart'] = cart
    
    #Give feedback and redirect
    flash('Item added to cart!')
    return redirect(request.referrer or '/products') # Go back to where they were


@bp.route('/cart')
def view_cart():
    #Get the cart
    cart = session.get('cart', {})
    
    #If the cart is empty, just show empty page
    if not cart:
        return render_template('cart.html', items=[], total=0)

    #Get the actual Product objects from the Database
    #We need to filter for products whose IDs are in our cart keys
    product_ids = [int(id) for id in cart.keys()]
    products = Product.query.filter(Product.id.in_(product_ids)).all()

    #Prepare the data for the template
    #We want a list of items where each item has (Product, Quantity, Subtotal)
    cart_items = []
    grand_total = 0

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        grand_total += subtotal
        
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render_template('cart.html', items=cart_items, total=grand_total)

@bp.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    str_id = str(product_id)
    
    # If the item is in the cart, remove it using .pop()
    if str_id in cart:
        cart.pop(str_id)
        session['cart'] = cart
        flash('Item removed from cart.')
        
    return redirect('/cart')

@bp.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = session.get('cart', {})
    str_id = str(product_id)
    
    # Get the new quantity from the submitted form
    # We use int() to make sure it's a number
    new_quantity = int(request.form.get('quantity', 1))
    
    if str_id in cart:
        if new_quantity > 0:
            cart[str_id] = new_quantity
            flash('Cart updated.')
        else:
            # If they change the quantity to 0, just remove it entirely
            cart.pop(str_id)
            flash('Item removed from cart.')
            
        session['cart'] = cart
        
    return redirect('/cart')

@bp.context_processor
def inject_cart_count():
    # Get the cart from the session, default to empty dict if it doesn't exist
    cart = session.get('cart', {})
    
    # The cart is a dictionary like {'product_id': quantity}
    # We want to sum all the quantities (the values)
    total_items = sum(cart.values())
    
    # This makes 'cart_count' available in ALL your HTML files automatically!
    return dict(cart_count=total_items)

# ---------- CART ----------
@bp.route('/checkout')
def checkout():
    #First make sure they are logged in
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to place an order.', 'warning')
        return redirect('/login')

    #Gets the cart
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!', 'warning')
        return redirect('/products')

    #Create an empty Order 
    new_order = Order(user_id=user_id, total_price=0)
    db.session.add(new_order)
    db.session.flush() #Assigns an ID to new_order without saving it yet

    grand_total = 0

    try:
        # Looping through the cart and process each item
        for str_product_id, quantity in cart.items():
            
            #Fetch product and lock the row in MySQL
            product = Product.query.filter_by(id=int(str_product_id)).with_for_update().first()

            # Reduce the stock and make sure to prevent overselling
            if product.stock < quantity:
                db.session.rollback() # Cancel the entire transaction and release the lock!
                flash(f'Sorry, we only have {product.stock} of {product.name} left in stock.', 'danger')
                return redirect('/cart')
            
            #Deduct the stock
            product.stock -= quantity

            #Calculate price and add to grand total
            subtotal = product.price * quantity
            grand_total += subtotal

            #Create the OrderItem to link the Product to the Order 
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                quantity=quantity,
                price_at_purchase=product.price 
            )
            db.session.add(order_item)

        #Take the order total and commit to the database
        new_order.total_price = grand_total
        db.session.commit() # ALL changes are saved here, and the LOCK IS RELEASED

    except Exception as e:
        #If anything crashes, undo everything and release locks
        db.session.rollback()
        flash('An error occurred while processing your order. Please try again.', 'danger')
        return redirect('/cart')

    #Clearing the cart from the session since they bought the items
    session.pop('cart', None)

    flash('Order placed successfully! Thank you for your purchase.', 'success')
    return redirect('/products')
# ---------- Order History ----------
#Customer
@bp.route('/orders')
def my_orders():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your orders.', 'warning')
        return redirect('/login')

    #Fetch the orders belonging to this specific user, starting with the latest order
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.date.desc()).all()
    
    # THen we pass admin_view=False so the template knows it's a customer
    return render_template('orders.html', orders=orders, admin_view=False)

#Admin
@bp.route('/admin/orders')
def all_orders():
    user_id = session.get('user_id')
    role = session.get('role')
    
    #Check if curren user is admin
    if not user_id or role.lower() != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect('/login')

    #Fetch all the orders in the database, the latest first
    orders = Order.query.order_by(Order.date.desc()).all()
    
    # Then we pass admin_view=True so the template can show some extra info 
    return render_template('orders.html', orders=orders, admin_view=True)

# ---------- Review ----------
@bp.post("/products/<int:product_id>/review")
def add_review(product_id: int):
    #Check if the user is logged in
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in to leave a review.", "warning")
        return redirect("/login")

    #Get the product and the form data
    product = Product.query.get_or_404(product_id)
    rating_raw = request.form.get("rating")
    comment = request.form.get("comment", "").strip()

    has_purchased = OrderItem.query.join(Order).filter(
        Order.user_id == user_id,
        OrderItem.product_id == product_id
    ).first()

    if not has_purchased:
        flash("You can only review products that you have actually purchased!", "danger")
        return redirect(f"/products/{product_id}")

    #Validate the rating (must be between 1 and 5)
    try:
        rating = int(rating_raw)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        flash("Invalid rating. Please select 1 to 5 stars.", "danger")
        return redirect(f"/products/{product_id}")

    #Create and save the review
    new_review = Review(
        user_id=user_id, 
        product_id=product.id, 
        rating=rating, 
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()

    flash("Thank you for your review!", "success")
    return redirect(f"/products/{product_id}")

@bp.post("/reviews/<int:review_id>/delete")
def delete_review(review_id):
    #Admins only
    if session.get("role") != "admin":
        flash("Unauthorized access. Admins only.", "danger")
        return redirect("/")

    #Find the review in the database
    review = Review.query.get_or_404(review_id)
    
    #Save the product_id so we know where to redirect the admin afterwards
    product_id = review.product_id

    #Simply delete it and commit to the database
    db.session.delete(review)
    db.session.commit()

    flash("Review deleted successfully.", "success")
    return redirect(f"/products/{product_id}")
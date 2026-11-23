
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection, create_tables

app = Flask(__name__)
app.secret_key = "change-this-secret-key"


@app.route('/')
def home():
    search = request.args.get('search', '').strip()

    con = get_connection()
    cur = con.cursor(dictionary=True)

    if search:
        cur.execute(
            "SELECT * FROM products WHERE name LIKE %s OR description LIKE %s",
            ('%' + search + '%', '%' + search + '%')
        )
    else:
        cur.execute("SELECT * FROM products")

    products = cur.fetchall()

    cur.close()
    con.close()

    return render_template('index.html', products=products)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        con = get_connection()
        cur = con.cursor()

        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            con.close()
            flash("Email already registered!")
            return redirect(url_for('register'))

        cur.execute(
            "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
            (username, email, password, 'user')
        )

        con.commit()
        cur.close()
        con.close()

        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        con = get_connection()
        cur = con.cursor(dictionary=True)

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        cur.close()
        con.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            return redirect(url_for('admin' if user['role'] == 'admin' else 'home'))

        flash("Invalid email or password!")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cur.fetchone()

    cur.close()
    con.close()

    if not product:
        flash("Product not found!")
        return redirect(url_for('home'))

    cart = session.get('cart', {})
    product_key = str(product_id)
    quantity = int(cart.get(product_key, 0))

    if quantity >= product['stock']:
        flash("Not enough stock available!")
    else:
        cart[product_key] = quantity + 1
        session['cart'] = cart
        flash("Product added to cart!")

    return redirect(url_for('home'))


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cart_items = session.get('cart', {})
    products = []
    total = 0

    con = get_connection()
    cur = con.cursor(dictionary=True)

    for product_id, quantity in cart_items.items():
        cur.execute("SELECT * FROM products WHERE id=%s", (int(product_id),))
        product = cur.fetchone()

        if product:
            product['quantity'] = quantity
            product['subtotal'] = float(product['price']) * quantity
            total += product['subtotal']
            products.append(product)

    cur.close()
    con.close()

    return render_template('cart.html', products=products, total=total)


@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart

    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cart_items = session.get('cart', {})

    if not cart_items:
        flash("Your cart is empty!")
        return redirect(url_for('cart'))

    con = get_connection()
    cur = con.cursor(dictionary=True)

    total = 0
    order_products = []

    for product_id, quantity in cart_items.items():
        cur.execute("SELECT * FROM products WHERE id=%s", (int(product_id),))
        product = cur.fetchone()

        if not product or product['stock'] < quantity:
            cur.close()
            con.close()
            flash("Some products are out of stock!")
            return redirect(url_for('cart'))

        total += float(product['price']) * quantity
        order_products.append((product, quantity))

    cur.execute(
        "INSERT INTO orders (user_id, total, status) VALUES (%s, %s, %s)",
        (session['user_id'], total, 'Placed')
    )

    order_id = cur.lastrowid

    for product, quantity in order_products:
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, product['id'], quantity, product['price'])
        )

        cur.execute(
            "UPDATE products SET stock = stock - %s WHERE id=%s",
            (quantity, product['id'])
        )

    con.commit()
    cur.close()
    con.close()

    session['cart'] = {}
    flash("Order placed successfully!")

    return redirect(url_for('orders'))


@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM orders WHERE user_id=%s ORDER BY id DESC",
        (session['user_id'],)
    )

    orders_list = cur.fetchall()

    cur.close()
    con.close()

    return render_template('orders.html', orders=orders_list)


@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT * FROM products ORDER BY id DESC")
    products = cur.fetchall()

    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    orders_list = cur.fetchall()

    cur.close()
    con.close()

    return render_template(
        'admin.html',
        products=products,
        orders=orders_list
    )


@app.route('/add_product', methods=['POST'])
def add_product():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    image = request.form['image']
    stock = request.form['stock']

    con = get_connection()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO products (name, description, price, image, stock) VALUES (%s, %s, %s, %s, %s)",
        (name, description, price, image, stock)
    )

    con.commit()
    cur.close()
    con.close()

    flash("Product added successfully!")
    return redirect(url_for('admin'))


@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    con = get_connection()
    cur = con.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.form['image']
        stock = request.form['stock']

        cur.execute(
            """UPDATE products
               SET name=%s, description=%s, price=%s, image=%s, stock=%s
               WHERE id=%s""",
            (name, description, price, image, stock, product_id)
        )

        con.commit()
        cur.close()
        con.close()

        flash("Product updated successfully!")
        return redirect(url_for('admin'))

    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cur.fetchone()

    cur.close()
    con.close()

    if not product:
        flash("Product not found!")
        return redirect(url_for('admin'))

    return render_template('edit_product.html', product=product)


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    con = get_connection()
    cur = con.cursor()

    cur.execute("DELETE FROM products WHERE id=%s", (product_id,))

    con.commit()
    cur.close()
    con.close()

    flash("Product deleted successfully!")
    return redirect(url_for('admin'))


@app.route('/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    status = request.form.get('status')
    print("Received order status:", status)

    con = get_connection()
    cur = con.cursor()

    try:
        cur.execute(
            "UPDATE orders SET status=%s WHERE id=%s",
            (status, order_id)
        )

        print("Rows updated:", cur.rowcount)

        con.commit()
        flash("Order status updated successfully!")

    except Exception as e:
        con.rollback()
        print("Order update error:", e)
        flash("Order status update failed!")

    finally:
        cur.close()
        con.close()

    return redirect(url_for('admin'))


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)

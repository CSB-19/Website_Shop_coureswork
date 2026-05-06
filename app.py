from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "courseworksecret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products.db"
db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(500))
    price = db.Column(db.Float)
    image = db.Column(db.String(100))
    impact = db.Column(db.Float)


def get_detailed_description(product):
    if product.id == 1:
        return "This pen is inspired by Muhammad Ali, one of the greatest boxers of all time. Ali became Heavyweight Champion at a young age and was known for his confidence, speed and personality. The design links to his boxing career, including the Rumble in the Jungle fight, boxing hand wraps, a butterfly detail, and a championship belt style clip."
    elif product.id == 2:
        return "This pen is inspired by Enzo Ferrari and his connection to luxury sports cars. The design is based on speed, racing and Italian style. It is a special edition pen for collectors who are interested in Ferrari history and high quality writing instruments."
    elif product.id == 3:
        return "This pen is inspired by Gustav Klimt, who was famous for decorative artwork and gold patterns. The design links to his artistic style and gives the pen a more creative and colourful look. It is aimed at people who enjoy art as well as luxury pens."
    elif product.id == 4:
        return "This pen is inspired by Queen Elizabeth II and is designed as a tribute to her long reign. It has a formal and traditional style, making it suitable as a collectable item. The pen is meant to represent history, royalty and British heritage."
    else:
        return product.description


# Route for the homepage
@app.route("/")
def home():
    sort_by = request.args.get("sort")

    query = Product.query

    if sort_by == "name":
        query = query.order_by(Product.name)
    elif sort_by == "price":
        query = query.order_by(Product.price)
    elif sort_by == "impact":
        query = query.order_by(Product.impact)

    products = query.all()

    return render_template(
        "home.html",
        products=products,
        sort_by=sort_by,
    )


# Page for products
@app.route("/product/<int:id>")
def product(id):
    product = Product.query.get(id)
    detailed_description = get_detailed_description(product)
    second_image = product.image.replace(".jpg", "2.jpg")

    return render_template(
        "product.html",
        product=product,
        detailed_description=detailed_description,
        second_image=second_image
    )


@app.route("/product_info/<int:id>")
def product_info(id):
    product = Product.query.get(id)

    return jsonify({
        "name": product.name,
        "description": get_detailed_description(product),
        "price": product.price,
        "impact": product.impact
    })


# Adding to the basket
@app.route("/add_to_basket/<int:id>", methods=["POST"])
def add_to_basket(id):

    quantity = request.form.get("quantity", "1")

    if not quantity.isdigit() or int(quantity) < 1:
        quantity = 1
    else:
        quantity = int(quantity)

    if "basket" not in session:
        session["basket"] = {}

    basket = session["basket"]

    if str(id) in basket:
        basket[str(id)] += quantity
    else:
        basket[str(id)] = quantity

    session["basket"] = basket

    return redirect(url_for("basket"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "basket" not in session or len(session["basket"]) == 0:
        return redirect("/")  # redirect if basket is empty

    basket = session["basket"]
    products = []
    total = 0

    for product_id, quantity in basket.items():
        product = Product.query.get(int(product_id))
        if product is None:
            continue
        subtotal = product.price * quantity
        total += subtotal
        products.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal
        })

    if request.method == "POST":
        name = request.form.get("name")
        card_number = request.form.get("card_number")
        expiry = request.form.get("expiry")
        cvv = request.form.get("cvv")

        errors = []

        # Validation
        if not name or not card_number or not expiry or not cvv:
            errors.append("All fields are required.")
        cleaned_card_number = card_number.replace(" ", "").replace("-", "")

        if not cleaned_card_number.isdigit() or len(cleaned_card_number) != 16:
            errors.append("Credit card number must be 16 digits.")
        if not cvv.isdigit() or len(cvv) != 3:
            errors.append("CVV must be 3 digits.")

        if errors:
            return render_template("checkout.html", products=products, total=total, errors=errors)
        else:
            # Clearing the basket after successful checkout
            session["basket"] = {}
            return render_template("checkout_success.html", total=total, name=name)

    return render_template("checkout.html", products=products, total=total)


# Page for the Basket
@app.route("/basket")
def basket():

    basket = session.get("basket", {})
    products_in_basket = []
    total = 0

    for product_id, quantity in basket.items():

        product = Product.query.get(int(product_id))
        if product is None:
            continue

        subtotal = product.price * quantity
        total += subtotal

        products_in_basket.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal
        })

    return render_template("basket.html", products=products_in_basket, total=total)


# Remove item from the basket
@app.route("/remove/<int:id>")
def remove(id):

    basket = session.get("basket", {})

    if str(id) in basket:
        del basket[str(id)]

    session["basket"] = basket

    return redirect(url_for("basket"))


@app.route("/clear_basket")
def clear_basket():
    session["basket"] = {}
    return redirect(url_for("basket"))

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        if Product.query.count() == 0:

            p1 = Product(
                name="Muhammad Ali Limited Edition Fountain Pen",
                description="A tribute to Muhammad Ali's legacy.",
                image="Ali.jpg",
                price=4100.00,
                impact=2.4  # kg CO₂
            )

            p2 = Product(
                name="Enzo Ferrari Special Edition Fountain Pen",
                description="A tribute to Enzo Ferrari's legacy.",
                image="Enzo.jpg",
                price=1250.00,
                impact=1.8  # kg CO₂
            )

            p3 = Product(
                name="Gustav Klimt Limited Edition Fountain Pen",
                description="Inspired by the artwork of Gustav Klimt.",
                image="Gustav.jpg",
                price=3540.00,
                impact=3.1  # kg CO₂
            )

            p4 = Product(
                name="Queen Special Edition Fountain Pen",
                description="A tribute to Queen Elizabeth II.",
                image="Queen.jpg",
                price=1250.00,
                impact=2.0  # kg CO₂
            )
            db.session.add_all([p1, p2, p3, p4])
            db.session.commit()

    app.run(debug=True)

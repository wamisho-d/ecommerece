from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_limiter import Limiter
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, verify_jwt_in_request
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime
from functools import wraps
import unittest
from unittest.mock import patch

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/db_name'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'simple'
    JWT_SECRET_KEY = 'super-secret-key'
    RATELIMIT_DEFAULT = "100 per day"

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
cache = Cache(app)
limiter = Limiter(app)
jwt = JWTManager(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    account = db.relationship('CustomerAccount', backref='customer', uselist=False)

class CustomerAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer', backref='orders')
    products = db.relationship('OrderProduct', backref='order')

class OrderProduct(db.Model):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify(msg='Admins only!'), 403
        return fn(*args, **kwargs)
    return wrapper

def create_customer(data):
    customer = Customer(name=data['name'], email=data['email'], phone_number=data['phone_number'])
    db.session.add(customer)
    db.session.commit()
    return customer

def get_customer(customer_id):
    return Customer.query.get(customer_id)

def update_customer(customer_id, data):
    customer = Customer.query.get(customer_id)
    if customer:
        customer.name = data['name']
        customer.email = data['email']
        customer.phone_number = data['phone_number']
        db.session.commit()
    return customer

def delete_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        db.session.delete(customer)
        db.session.commit()
    return customer

def create_customer_account(customer_id, data):
    account = CustomerAccount(username=data['username'], password_hash=data['password'], customer_id=customer_id)
    db.session.add(account)
    db.session.commit()
    return account

def get_customer_account(account_id):
    return CustomerAccount.query.get(account_id)

def update_customer_account(account_id, data):
    account = CustomerAccount.query.get(account_id)
    if account:
        account.username = data['username']
        account.password_hash = data['password']
        db.session.commit()
    return account

def delete_customer_account(account_id):
    account = CustomerAccount.query.get(account_id)
    if account:
        db.session.delete(account)
        db.session.commit()
    return account

def create_product(data):
    product = Product(name=data['name'], price=data['price'])
    db.session.add(product)
    db.session.commit()
    return product

def get_product(product_id):
    return Product.query.get(product_id)

def update_product(product_id, data):
    product = Product.query.get(product_id)
    if product:
        product.name = data['name']
        product.price = data['price']
        db.session.commit()
    return product

def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return product

def list_products():
    return Product.query.all()

def place_order(customer_id, data):
    order = Order(order_date=datetime.utcnow(), customer_id=customer_id)
    db.session.add(order)
    db.session.flush()  

    for item in data['items']:
        order_product = OrderProduct(order_id=order.id, product_id=item['product_id'], quantity=item['quantity'])
        db.session.add(order_product)

    db.session.commit()
    return order

def get_order(order_id):
    return Order.query.get(order_id)

@admin_required
def create_customer_endpoint():
    data = request.json
    customer = create_customer(data)
    return jsonify(customer), 201

@admin_required
def get_customer_endpoint(customer_id):
    customer = get_customer(customer_id)
    return jsonify(customer)

@admin_required
def update_customer_endpoint(customer_id):
    data = request.json
    customer = update_customer(customer_id, data)
    return jsonify(customer)

@admin_required
def delete_customer_endpoint(customer_id):
    delete_customer(customer_id)
    return '', 204

@admin_required
def create_customer_account_endpoint(customer_id):
    data = request.json
    account = create_customer_account(customer_id, data)
    return jsonify(account), 201

@admin_required
def get_customer_account_endpoint(account_id):
    account = get_customer_account(account_id)
    return jsonify(account)

@admin_required
def update_customer_account_endpoint(account_id):
    data = request.json
    account = update_customer_account(account_id, data)
    return jsonify(account)

@admin_required
def delete_customer_account_endpoint(account_id):
    delete_customer_account(account_id)
    return '', 204

@admin_required
def create_product_endpoint():
    data = request.json
    product = create_product(data)
    return jsonify(product), 201

def get_product_endpoint(product_id):
    product = get_product(product_id)
    return jsonify(product)

@admin_required
def update_product_endpoint(product_id):
    data = request.json
    product = update_product(product_id, data)
    return jsonify(product)

@admin_required
def delete_product_endpoint(product_id):
    delete_product(product_id)
    return '', 204

def list_products_endpoint():
    products = list_products()
    return jsonify(products)

@jwt_required()
def place_order_endpoint(customer_id):
    data = request.json
    order = place_order(customer_id, data)
    return jsonify(order), 201

@jwt_required()
def get_order_endpoint(order_id):
    order = get_order(order_id)
    return jsonify(order)

customer_bp = Blueprint('customer_bp', __name__)
customer_bp.route('', methods=['POST'])(create_customer_endpoint)
customer_bp.route('/<int:customer_id>', methods=['GET'])(get_customer_endpoint)
customer_bp.route('/<int:customer_id>', methods=['PUT'])(update_customer_endpoint)
customer_bp.route('/<int:customer_id>', methods=['DELETE'])(delete_customer_endpoint)
customer_bp.route('/<int:customer_id>/accounts', methods=['POST'])(create_customer_account_endpoint)
customer_bp.route('/accounts/<int:account_id>', methods=['GET'])(get_customer_account_endpoint)
customer_bp.route('/accounts/<int:account_id>', methods=['PUT'])(update_customer_account_endpoint)
customer_bp.route('/accounts/<int:account_id>', methods=['DELETE'])(delete_customer_account_endpoint)
app.register_blueprint(customer_bp, url_prefix='/customers')

product_bp = Blueprint('product_bp', __name__)
product_bp.route('', methods=['POST'])(create_product_endpoint)
product_bp.route('/<int:product_id>', methods=['GET'])(get_product_endpoint)
product_bp.route('/<int:product_id>', methods=['PUT'])(update_product_endpoint)
product_bp.route('/<int:product_id>', methods=['DELETE'])(delete_product_endpoint)
product_bp.route('', methods=['GET'])(list_products_endpoint)
app.register_blueprint(product_bp, url_prefix='/products')

order_bp = Blueprint('order_bp', __name__)
order_bp.route('/<int:customer_id>', methods=['POST'])(place_order_endpoint)
order_bp.route('/<int:order_id>', methods=['GET'])(get_order_endpoint)
app.register_blueprint(order_bp, url_prefix='/orders')

SWAGGER_URL = '/api/docs'
API_URL = '/swagger.yaml'
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "E-commerce API"}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

swagger_yaml = '''
openapi: "3.0.0"
info:
  title: "E-commerce API"
  version: "1.0.0"
paths:
  /customers:
    post:
      summary: "Create a new customer"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
                phone_number:
                  type: string
      responses:
        '201':
          description: "Customer created"
  /customers/{customer_id}:
    get:
      summary: "Get customer by ID"
      parameters:
        - name: "customer_id"
          in: "path"
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: "Customer details"
    put:
      summary: "Update customer by ID"
      parameters:
        - name: "customer_id"
          in: "path"
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
                phone_number:
                  type: string
      responses:
        '200':
          description: "Customer updated"
    delete:
      summary: "Delete customer by ID"
      parameters:
        - name: "customer_id"
          in: "path"
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: "Customer deleted"
  /customers/{customer_id}/accounts:
    post:
      summary: "Create a new customer account"
      parameters:
        - name: "customer_id"
          in: "path"
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
      responses:
        '201':
          description: "Customer account created"
  /customers/accounts/{account_id}:
    get:
      summary: "Get customer account by ID"
      parameters:
        - name: "account_id"
          in: "path"
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: "Customer account details"
    put:
      summary: "Update customer account by ID"
      parameters:
        - name: "account_id"
          in: "path"
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                username:
                  type: string
                password:
                  type: string
      responses:
        '200':
          description: "Customer account updated"
    delete:
      summary: "Delete customer account by ID"
      parameters:
        - name: "account_id"
          in: "path"
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: "Customer account deleted"
  /products:
    post:
      summary: "Create a new product"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                price:
                  type: number
      responses:
        '201':
          description: "Product created"
    get:
      summary: "List all products"
      responses:
        '200':
          description: "A list of products"
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                    name:
                      type: string
                    price:
                      type: number
  /products/{product_id}:
    get:
      summary: "Get product by ID"
      parameters:
        - name: "product_id"
          in: "path"
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: "Product details"
    put:
      summary: "Update product by ID"
      parameters:
        - name: "product_id"
          in: "path"
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                price:
                  type: number
      responses:
        '200':
          description: "Product updated"
    delete:
      summary: "Delete product by ID"
      parameters:
        - name: "product_id"
          in: "path"
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: "Product deleted"
  /orders:
    post:
      summary: "Place a new order"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                customer_id:
                  type: integer
                items:
                  type: array
                  items:
                    type: object
                    properties:
                      product_id:
                        type: integer
                      quantity:
                        type: integer
      responses:
        '201':
          description: "Order placed"
  /orders/{order_id}:
    get:
      summary: "Get order by ID"
      parameters:
        - name: "order_id"
          in: "path"
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: "Order details"
'''

@app.route('/swagger.yaml')
def swagger_yaml_route():
    return swagger_yaml, 200, {'Content-Type': 'text/plain'}

class CustomerTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('run.create_customer')
    def test_create_customer(self, mock_create_customer):
        mock_create_customer.return_value = Customer(id=1, name="Thomas Jack", email="thomas@gmail.com", phone_number="3234562345")
        response = self.app.post('/customers', json={"name": "Thomas Jack", "email": "thomas@gmail.com", "phone_number": "3234562345"})
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Thomas Jack', response.data)

    @patch('run.get_customer')
    def test_get_customer(self, mock_get_customer):
        mock_get_customer.return_value = Customer(id=1, name="Thomas Jack", email="thomas@gmail.com", phone_number="3234562345")
        response = self.app.get('/customers/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thomas Jack', response.data)

    @patch('run.update_customer')
    def test_update_customer(self, mock_update_customer):
        mock_update_customer.return_value = Customer(id=1, name="Thomas Jack", email="thomas@gmail.com", phone_number="3234562345")
        response = self.app.put('/customers/1', json={"name": "Thomas Jack", "email": "thomas@gmail.com", "phone_number": "3234562345"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thomas Jack', response.data)

    @patch('run.delete_customer')
    def test_delete_customer(self, mock_delete_customer):
        response = self.app.delete('/customers/1')
        self.assertEqual(response.status_code, 204)

class ProductTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('run.create_product')
    def test_create_product(self, mock_create_product):
        mock_create_product.return_value = Product(id=1, name="Product1", price=25000.0)
        response = self.app.post('/products', json={"name": "Product1", "price": 2500.0})
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Product1', response.data)

    @patch('run.get_product')
    def test_get_product(self, mock_get_product):
        mock_get_product.return_value = Product(id=1, name="Product1", price=2500.0)
        response = self.app.get('/products/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Product1', response.data)

    @patch('run.update_product')
    def test_update_product(self, mock_update_product):
        mock_update_product.return_value = Product(id=1, name="Product1", price=2500.0)
        response = self.app.put('/products/1', json={"name": "Product1", "price": 2500.0})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Product1', response.data)

    @patch('run.delete_product')
    def test_delete_product(self, mock_delete_product):
        response = self.app.delete('/products/1')
        self.assertEqual(response.status_code, 204)

    class OrderTestCase(unittest.TestCase):

     def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('app.services.order_service.place_order')
    def test_place_order(self, mock_place_order):
        mock_place_order.return_value = Order(id=1, order_date="2025-03-30", customer_id=1)
        response = self.client.post('/orders/1', json={"items": [{"product_id": 1, "quantity": 2}]})
        self.assertEqual(response.status_code, 201)

    @patch('app.services.order_service.get_order')
    def test_get_order(self, mock_get_order):
        mock_get_order.return_value = Order(id=1, order_date="2025-03-30", customer_id=1)
        response = self.client.get('/orders/1')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    app.run(debug=True)
















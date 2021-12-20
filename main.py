import datetime

from flask import Flask, request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taxi.sqlite"
db = SQLAlchemy(app)


# db.create_all()


class Drivers(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    car = db.Column(db.String(100), nullable=False)

    def __init__(self, name, car):
        self.name = name
        self.car = car


class Clients(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_vip = db.Column(db.Boolean, nullable=False)

    def __init__(self, name, is_vip):
        self.name = name
        self.is_vip = is_vip


class Orders(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    address_from = db.Column(db.String(100), nullable=False)
    address_to = db.Column(db.String(100), nullable=False)
    client_id = db.Column(db.Integer, nullable=False)
    driver_id = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(), nullable=False)

    def __init__(self, address_from, address_to, client_id, driver_id, date_created, status):
        self.address_from = address_from
        self.address_to = address_to
        self.client_id = client_id
        self.driver_id = driver_id
        self.date_created = date_created
        self.status = status


@app.route('/drivers/<int:id>', methods=['GET'])
def get_driver_by_id(id):
    driver = Drivers.query.filter_by(id=id).first_or_404()
    data = {"id": driver.id,
            "name": driver.name,
            "car": driver.car}
    return jsonify(data), 200


@app.route('/drivers', methods=['POST'])
def create_driver():
    json = request.get_json()
    driver = Drivers(name=json.get('name'), car=json.get('car'))
    db.session.add(driver)
    db.session.commit()
    return f"Водитель добавлен c данными: id : {driver.id}", 201


@app.route('/drivers/<int:id>', methods=['DELETE'])
def delete_driver(id):
    deleted_driver = Drivers.query.filter_by(id=id).first_or_404()
    db.session.delete(deleted_driver)
    db.session.commit()
    return f"Удален водитель с id : {id}", 204


@app.route('/clients/<int:id>', methods=['GET'])
def get_client_by_id(id):
    client = Clients.query.filter_by(id=id).first_or_404()
    data = {"id": client.id,
            "name": client.name,
            "is_vip": client.is_vip}
    return jsonify(data), 200


@app.route('/clients', methods=['POST'])
def create_client():
    json = request.get_json()
    client = Clients(name=json.get('name'), is_vip=json.get('is_vip'))
    db.session.add(client)
    db.session.commit()
    return f"Клиент добавлен c данными: id : {client.id}", 201


@app.route('/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    deleted_client = Clients.query.filter_by(id=id).first_or_404()
    db.session.delete(deleted_client)
    db.session.commit()
    return f"Удален клиент с id : {id}", 204


@app.route('/orders', methods=['POST'])
def create_order():
    json = request.get_json()
    client_id = json.get('client_id')
    driver_id = json.get('driver_id')
    client = Clients.query.filter_by(id=client_id).first()
    driver = Drivers.query.filter_by(id=driver_id).first()
    if client is not None and driver is not None:
        order = Orders(address_from=json.get('address_from'),
                       address_to=json.get('address_to'),
                       client_id=json.get('client_id'),
                       driver_id=json.get('driver_id'),
                       date_created=datetime.datetime.now(),
                       status='not_accepted')
        db.session.add(order)
        db.session.commit()
        return f"Заказ добавлен c данными: id : {order.id}", 201
    else:
        return "Водитель/клиент не найден", 404


@app.route('/orders/<id>', methods=['PUT'])
def update_order(id):
    json = request.get_json()
    order = Orders.query.filter_by(id=id).first_or_404()
    if order.status == 'not_accepted':
        order.address_from = json.get('address_from')
        order.address_to = json.get('address_to')
        order.client_id = json.get('client_id')
        order.driver_id = json.get('driver_id')
        order.date_created = datetime.datetime.now()
        db.session.commit()
        return f"Заказ c id : {order.id} отредактирован", 200

    else:
        return "Заказ не может быть изменен", 400


@app.route('/orders/<id>/change-status', methods=['PUT'])
def change_order_status(id):
    json = request.get_json()
    new_status = json.get('status')
    order = Orders.query.filter_by(id=id).first_or_404()
    if order.status == 'not_accepted':
        if new_status in ('not_accepted', 'in_progress', 'cancelled'):
            order.status = new_status
            db.session.commit()
            return f"Статус заказа с id: {order.id} успешно изменен на {new_status}", 200
        elif new_status == 'done':
            return f"Статус заказа с id: {order.id} не может быть изменен на {new_status}", 400
        else:
            return "Неверный статус заказа", 400

    elif order.status == 'in_progress':
        if new_status in ('in_progress', 'cancelled', 'done'):
            order.status = new_status
            db.session.commit()
            return f"Статус заказа с id: {order.id} успешно изменен на {new_status}", 200
        elif new_status == 'not_accepted':
            return f"Статус заказа с id: {order.id} НЕ может быть изменен на {new_status}", 400
        else:
            return "Неверный статус заказа", 400

    elif order.status in ('done', 'cancelled'):
        if new_status in ('in_progress', 'cancelled', 'done', 'not_accepted'):
            return f"Статус заказа с id: {order.id} НЕ может быть изменен на {new_status}", 400
        else:
            return "Неверный статус заказа", 400


@app.route('/orders/<int:id>', methods=['GET'])
def get_order_by_id(id):
    order = Orders.query.filter_by(id=id).first_or_404()
    data = {"id": order.id,
            "client_id": order.client_id,
            "driver_id": order.driver_id,
            "date_created": order.date_created,
            "status": order.status,
            "address_from": order.address_from,
            "address_to": order.address_to}
    return data, 200

from app.repositories import supplier_repo
from app.validators import validate_supplier_form


def list_suppliers():
    return supplier_repo.list_suppliers()


def get_supplier(supplier_id):
    return supplier_repo.get_supplier(supplier_id)


def create_supplier_from_form(form):
    data = validate_supplier_form(form)
    supplier_repo.create_supplier(data['name'], data['email'])


def update_supplier_from_form(supplier_id, form):
    data = validate_supplier_form(form)
    supplier_repo.update_supplier(supplier_id, data['name'], data['email'])


def delete_supplier(supplier_id):
    supplier_repo.delete_supplier(supplier_id)

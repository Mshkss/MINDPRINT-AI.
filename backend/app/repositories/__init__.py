from sqlalchemy import inspect


def serialize(row):
    return {
        column.key: getattr(row, column.key)
        for column in inspect(row).mapper.column_attrs
    }


def public_user(user):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

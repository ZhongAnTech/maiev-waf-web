import datetime as dt
from sqlalchemy import func, desc
from app import db
utcnow = dt.datetime.utcnow


class CRUDMixin(object):
    """Mixin that adds` convenience methods for CRUD (create, read, update, delete) operations."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()

    @classmethod
    def get_by_page(cls, query, page, per_page):
        return cls.query.filter_by(**query).paginate(page, per_page, False)

    @classmethod
    def get_by_filter_by(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    @classmethod
    def get_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

class CompatibleModel(CRUDMixin, db.Model):
    __abstract__ = True







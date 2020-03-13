from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from labonneboite.common.database import db_session


class CRUDMixin(object):
    __table_args__ = {"extend_existing": True}

    @classmethod
    def create(cls, commit=True, **kwargs):
        instance = cls(**kwargs)
        return instance.save(commit=commit)

    @classmethod
    def get(cls, object_id):
        return cls.query.get(object_id)

    def save(self, commit=True):
        db_session.add(self)
        if commit:
            db_session.commit()
        return self

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def delete(self, commit=True):
        db_session.delete(self)
        return commit and db_session.commit()

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        try:
            return db_session.query(cls).filter_by(**kwargs).one(), False
        except NoResultFound:
            if defaults:
                kwargs.update(defaults)
            instance = cls(**kwargs)
            try:
                db_session.add(instance)
                db_session.commit()
                return instance, True
            except IntegrityError:
                db_session.rollback()
                return db_session.query(cls).filter_by(**kwargs).one(), True

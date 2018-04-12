# Database migration system

We use Alembic which is a lightweight database migration tool for usage with the SQLAlchemy Database Toolkit for Python.

## Alembic

- [Documentation](http://alembic.zzzcomputing.com/en/latest/)
- [Source](https://bitbucket.org/zzzeek/alembic)

## Creating migrations scripts

To create a new migration file:

1. Create an empty migration file: `alembic revision -m "your message, e.g. Add users table"`
2. Edit the generated migration file `upgrade` and `downgrade` methods according to the alembic API

## Using `autogenerate`

You can ease this process by running `alembic revision --autogenerate` and then perform a copy and paste of the code of interest.

For this method to work, however, the table must exists before running `alembic revision --autogenerate`:

    ipython

    from labonneboite.common.database import db_session, Base, engine
    from labonneboite.common.models import User
    Base.metadata.create_all(engine)

## Note about `constraints`

Sometimes you have to add things manually, e.g. some constraints are not auto-generated. Remember to compare your model with your migration file.

## Running migrations manually

You may need to run the migrations manually when developing a new feature:

- `alembic upgrade head` or just `make alembic_migrate`
- `alembic downgrade -1` or just `make alembic_rollback`

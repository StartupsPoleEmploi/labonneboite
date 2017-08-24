# Database migration system

We use Alembic which is a lightweight database migration tool for usage with the SQLAlchemy Database Toolkit for Python.

## Alembic

- [Documentation](http://alembic.zzzcomputing.com/en/latest/)
- [Source](https://bitbucket.org/zzzeek/alembic)

## Creating migrations scripts

Migrations scripts have to be created manually because some tables are dropped and created by the offices import process.

There is one table currently excluded from the migration system: **`etablissements`**.

To create a new migration file:

1. Connect to your Vagrant machine: `make vagrant_ssh_dev`
2. Create an empty migration file: `alembic revision -m "your message, e.g. Add users table"`
3. Edit the generated migration file `upgrade` and `downgrade` methods according to the alembic API

## Using `autogenerate`

You can ease this process by running `alembic revision --autogenerate` and then perform a copy and paste of the code of interest.

For this method to work, however, the table must exists before running `alembic revision --autogenerate`:

    make vagrant_ssh_dev

    ipython

    from labonneboite.common.database import db_session, Base, engine
    from labonneboite.common.models import User
    Base.metadata.create_all(engine)

## Note about `constraints`

Sometimes you have to add things manually, e.g. some constraints are not auto-generated. Remember to compare your model with your migration file.

## Running migrations manually

You may need to run the migrations manually when developing a new feature:

- `alembic upgrade head`
- `alembic downgrade -1`

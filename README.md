# Lunch Ordering System

This is a simple lunch ordering system provided as a convenience for the attendees of CppNow
conference in Aspen, CO.

## Prerequisites

[uv](https://docs.astral.sh/uv/getting-started/) is used to manage python dependencies.  Install
following the directions [here](https://docs.astral.sh/uv/getting-started/installation/).

You'll also need the following list of packages installed:

- docker
- sqlite3

You will also need a Stripe account to manage credit card/e-payment methods. You can put the
`STRIPE_PUBLIC_KEY` and `STRIPE_SECRET_KEY` variables in your environment, or in a local .env
file for usage.

## Development testing

You can run the application locally in a `uv` virtual environment with the following:

```sh
uv run gunicorn --bind 0.0.0.0:8000 wsgi:application
```

This will start the webserver locally, and you can interact with it on port 8000.  The application
accepts an environment variable called `DATA_DIR` where it will look for the lunch options, store
the flask sessions, and create the database.

## Docker image

You can create the docker image using the following from the project root:

```sh
docker build -t lunch:latest .
```

## Scripts

The scripts directory automates some common actions with looking at the orders in the database.

## Live

The live directory is a set of terraform that will create a deployment in Google Cloud.  It sets
up a network, and provisions a single instance to run the webserver.


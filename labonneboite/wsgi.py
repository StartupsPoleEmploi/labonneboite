from labonneboite.web import app
from labonneboite.common.env import ENV_DEVELOPMENT, get_current_env

if __name__ == "__main__":
    if get_current_env() == ENV_DEVELOPMENT:
        # Since March 2020, PE Connect no longer allows redirect_uri with port 5000, however port 8080 works.
        # Additionally 'localhost' works whereas '0.0.0.0' no longer does.
        app.run(host="localhost", port=8080, debug=True)
    else:
        app.run(host="0.0.0.0")

import logging
from chalice import Chalice
from chalicelib.networks import networks_endpoint


app = Chalice(app_name='alligator')
app.register_blueprint(networks_endpoint)
app.log.setLevel(logging.DEBUG)

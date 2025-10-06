from flask import Flask, request, jsonify
from config import get_config_class

app = Flask(__name__)

# Load .env file configurations
ConfigClass = get_config_class()
app.config.from_object(ConfigClass)

if __name__ == '__main__':
    app.run(debug=True)
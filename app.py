from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route("/")
def index():
    with open("productos.json", encoding="utf-8") as f:
        productos = json.load(f)
    return render_template("index.html", productos=productos)

if __name__ == "__main__":
    app.run(debug=True)

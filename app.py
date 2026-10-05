from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("lavouras.html")


@app.route("/custos")
def custos():
    return render_template("custos.html")


if __name__ == "__main__":
    app.run(debug=True)
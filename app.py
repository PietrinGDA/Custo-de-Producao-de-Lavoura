from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def conectar_banco():
    conexao = sqlite3.connect("lavouras.db")
    conexao.row_factory = sqlite3.Row
    return conexao

def criar_tabelas():
    conexao = conectar_banco()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS lavouras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cultura TEXT NOT NULL,
            ano INTEGER NOT NULL
        )
    """)

    conexao.commit()
    conexao.execute("""
    CREATE TABLE IF NOT EXISTS custos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lavoura_id INTEGER NOT NULL,
        descricao TEXT NOT NULL,
        categoria TEXT NOT NULL,
        valor REAL NOT NULL,
        data TEXT NOT NULL,
        FOREIGN KEY (lavoura_id) REFERENCES lavouras (id)
        )
    """)
    conexao.close()

@app.route("/", methods=["GET", "POST"])
def inicio():
    if request.method == "POST":
        nome = request.form["nome"]
        cultura = request.form["cultura"]
        ano = request.form["ano"]

        conexao = conectar_banco()
        conexao.execute(
            "INSERT INTO lavouras (nome, cultura, ano) VALUES (?, ?, ?)",
            (nome, cultura, ano)
        )
        conexao.commit()
        conexao.close()

        return redirect(url_for("inicio"))

    conexao = conectar_banco()
    lavouras = conexao.execute(
        "SELECT * FROM lavouras ORDER BY id DESC"
    ).fetchall()
    conexao.close()

    return render_template("lavouras.html", lavouras=lavouras)


@app.route("/custos", methods=["GET", "POST"])
def custos():
    conexao = conectar_banco()

    if request.method == "POST":
        lavoura_id = request.form["lavoura_id"]
        descricao = request.form["descricao"]
        categoria = request.form["categoria"]
        valor = request.form["valor"]
        data = request.form["data"]

        conexao.execute(
            """INSERT INTO custos
               (lavoura_id, descricao, categoria, valor, data)
               VALUES (?, ?, ?, ?, ?)""",
            (lavoura_id, descricao, categoria, valor, data)
        )
        conexao.commit()
        conexao.close()

        return redirect(url_for("custos"))

    lavouras = conexao.execute(
        "SELECT * FROM lavouras ORDER BY nome"
    ).fetchall()

    custos_cadastrados = conexao.execute("""
        SELECT custos.*, lavouras.nome AS nome_lavoura
        FROM custos
        JOIN lavouras ON custos.lavoura_id = lavouras.id
        ORDER BY custos.id DESC
    """).fetchall()

    conexao.close()

    return render_template(
        "custos.html",
        lavouras=lavouras,
        custos=custos_cadastrados
    )

@app.route("/consulta")
def consulta():
    lavoura = request.args.get("lavoura", "").strip()
    categoria = request.args.get("categoria", "").strip()
    data = request.args.get("data", "").strip()

    sql = """
        SELECT custos.*, lavouras.nome AS nome_lavoura
        FROM custos
        JOIN lavouras ON custos.lavoura_id = lavouras.id
        WHERE 1 = 1
    """
    parametros = []

    if lavoura:
        sql += " AND lavouras.nome LIKE ?"
        parametros.append(f"%{lavoura}%")

    if categoria:
        sql += " AND custos.categoria = ?"
        parametros.append(categoria)

    if data:
        sql += " AND custos.data = ?"
        parametros.append(data)

    sql += " ORDER BY custos.data DESC"

    conexao = conectar_banco()
    custos_encontrados = conexao.execute(
        sql, parametros
    ).fetchall()
    conexao.close()

    total = sum(custo["valor"] for custo in custos_encontrados)

    return render_template(
        "consulta.html",
        custos=custos_encontrados,
        total=total
    )

@app.route("/custos/editar/<int:id>", methods=["GET", "POST"])
def editar_custo(id):
    conexao = conectar_banco()

    custo = conexao.execute(
        "SELECT * FROM custos WHERE id = ?", (id,)
    ).fetchone()

    if custo is None:
        conexao.close()
        return "Custo não encontrado", 404

    if request.method == "POST":
        descricao = request.form["descricao"]
        categoria = request.form["categoria"]
        valor = request.form["valor"]
        data = request.form["data"]

        conexao.execute(
            """UPDATE custos
               SET descricao = ?, categoria = ?, valor = ?, data = ?
               WHERE id = ?""",
            (descricao, categoria, valor, data, id)
        )
        conexao.commit()
        conexao.close()

        return redirect(url_for("consulta"))

    conexao.close()
    return render_template("editar_custo.html", custo=custo)

    
@app.route("/custos/excluir/<int:id>", methods=["POST"])
def excluir_custo(id):
    conexao = conectar_banco()

    conexao.execute(
        "DELETE FROM custos WHERE id = ?",
        (id,)
    )

    conexao.commit()
    conexao.close()

    return redirect(url_for("consulta"))

    
@app.route("/lavouras/editar/<int:id>", methods=["GET", "POST"])
def editar_lavoura(id):
    conexao = conectar_banco()

    lavoura = conexao.execute(
        "SELECT * FROM lavouras WHERE id = ?", (id,)
    ).fetchone()

    if lavoura is None:
        conexao.close()
        return "Lavoura não encontrada", 404

    if request.method == "POST":
        nome = request.form["nome"]
        cultura = request.form["cultura"]
        ano = request.form["ano"]

        conexao.execute(
            """UPDATE lavouras
               SET nome = ?, cultura = ?, ano = ?
               WHERE id = ?""",
            (nome, cultura, ano, id)
        )
        conexao.commit()
        conexao.close()

        return redirect(url_for("inicio"))

    conexao.close()
    return render_template("editar_lavoura.html", lavoura=lavoura)

    
@app.route("/lavouras/excluir/<int:id>", methods=["POST"])
def excluir_lavoura(id):
    conexao = conectar_banco()

    custos = conexao.execute(
        "SELECT COUNT(*) FROM custos WHERE lavoura_id = ?",
        (id,)
    ).fetchone()[0]

    if custos > 0:
        conexao.close()
        return (
            "Não é possível excluir esta lavoura, "
            "pois existem custos associados a ela.",
            400
        )

    conexao.execute(
        "DELETE FROM lavouras WHERE id = ?",
        (id,)
    )

    conexao.commit()
    conexao.close()

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
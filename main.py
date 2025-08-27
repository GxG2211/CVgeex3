from flask import Flask, render_template, request, redirect, session, flash, send_file
import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
from PIL import Image
from reportlab.lib.utils import ImageReader

app = Flask(__name__)
app.secret_key = "clave-super-secreta"

USUARIOS_FILE = "usuarios.json"

def cargar_usuarios():
    if not os.path.exists(USUARIOS_FILE) or os.stat(USUARIOS_FILE).st_size == 0:
        return {}
    with open(USUARIOS_FILE, "r") as f:
        return json.load(f)

def guardar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios, f)

@app.route("/", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        confirmar = request.form["password_confirm"]

        if password != confirmar:
            flash("Las contraseñas no coinciden.")
            return redirect("/")

        usuarios = cargar_usuarios()

        if usuario in usuarios:
            flash("El usuario ya existe.")
            return redirect("/")

        usuarios[usuario] = {"password": password}
        guardar_usuarios(usuarios)
        session["usuario"] = usuario
        return redirect("/index")

    return render_template("registro.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        usuarios = cargar_usuarios()

        if usuario not in usuarios or usuarios[usuario]["password"] != password:
            flash("Usuario o contraseña incorrectos.")
            return redirect("/login")

        session["usuario"] = usuario
        return redirect("/index")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/index")
def index():
    if "usuario" not in session:
        return redirect("/login")
    return render_template("index.html")

@app.route("/generar", methods=["POST"])
def generar_cv():
    datos = request.form
    archivo_foto = request.files.get("foto")

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    azul = (0.2, 0.4, 0.8)

    # Encabezado con color
    pdf.setFillColorRGB(*azul)
    pdf.rect(0, height - 4*cm, width, 4*cm, fill=1, stroke=0)

    # Nombre y título
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(2*cm, height - 2.5*cm, datos["nombre"])

    pdf.setFont("Helvetica", 12)
    pdf.drawString(2*cm, height - 3.2*cm, datos["titulo"])

    # Insertar imagen si existe
    if archivo_foto and archivo_foto.filename != "":
        try:
            img = Image.open(archivo_foto)
            img = img.resize((100, 100))
            img_io = BytesIO()
            img.save(img_io, format="PNG")
            img_io.seek(0)
            pdf.drawImage(ImageReader(img_io), width - 4*cm, height - 3.5*cm, width=3*cm, height=3*cm, mask='auto')
        except:
            pass

    # Contacto
    y = height - 4.5*cm
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(2*cm, y, f"📍 {datos['ciudad']}     ✉ {datos['email']}     ☎ {datos['telefono']}")
    if datos["web"]:
        y -= 12
        pdf.drawString(2*cm, y, f"🔗 {datos['web']}")
    if datos["nacimiento"]:
        y -= 12
        pdf.drawString(2*cm, y, f"🎂 Nacimiento: {datos['nacimiento']}")
    y -= 20

    pdf.setStrokeColorRGB(*azul)
    pdf.setLineWidth(1)
    pdf.line(2*cm, y, width - 2*cm, y)
    y -= 16

    def bloque(titulo, contenido):
        nonlocal y
        if y < 5*cm:
            pdf.showPage()
            y = height - 3*cm
        pdf.setFont("Helvetica-Bold", 13)
        pdf.setFillColorRGB(*azul)
        pdf.drawString(2*cm, y, titulo)
        y -= 16
        pdf.setFont("Helvetica", 11)
        pdf.setFillColorRGB(0, 0, 0)
        for linea in contenido.split("\n"):
            pdf.drawString(2*cm, y, linea.strip())
            y -= 14
        y -= 8

    bloque("Perfil profesional", datos["perfil"])
    bloque("Educación", datos["educacion"])
    bloque("Experiencia laboral", datos["experiencia"])
    bloque("Habilidades", datos["habilidades"])
    bloque("Idiomas", datos["idiomas"])

    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.drawString(2*cm, 1.5*cm, "CV generado automáticamente por CVExpress.AI")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="mi_cv_con_foto.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)

"""Ponto de entrada. O Vercel detecta a variável `app` (WSGI) neste arquivo automaticamente.

Local:  python app.py   (ou: flask --app app run --debug)
"""
from laads import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)


---

## ⚡ Cómo correr el backend localmente

1. Instala Python 3.9+
2. Instala dependencias:
    ```
    pip install -r backend/requirements.txt
    ```
3. Crea el archivo `.env` en `/backend/` o configura tu variable de entorno `DATABASE_URL` con el string de conexión de PlanetScale o MySQL:
    ```
    DATABASE_URL="mysql+pymysql://usuario:clave@host/nombre_db"
    ```
4. Corre el backend:
    ```
    cd backend
    python app.py
    ```
   El backend estará disponible en [http://localhost:5000](http://localhost:5000)

---

## 🌐 Deploy en Render

1. Sube este proyecto a GitHub.
2. Crea un **Web Service** en [Render](https://render.com/), conectando este repo.
3. Setea la variable `DATABASE_URL` en "Environment" con tu string de PlanetScale.
4. Usa como "Start Command":
    ```
    gunicorn app:app
    ```

---

## 💻 Cómo probar el frontend

- Abre `frontend/index.html` en tu navegador.
- Asegúrate de que el backend esté corriendo y que el JS apunte a la URL correcta del backend (ajusta si usas otra ruta/base).
- Puedes subir el frontend a Netlify, Vercel, GitHub Pages, o cualquier servidor estático.

---

## 📂 Variables de entorno importantes

- `DATABASE_URL`: String de conexión a PlanetScale o MySQL
- `SECRET_KEY`: Secreto de Flask (opcional, para sesiones)

---

## 📚 Créditos y licencia

Desarrollado por [Tu Nombre o Empresa].  
Licencia MIT (puedes cambiar esto por la que prefieras).

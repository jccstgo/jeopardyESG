# 🎮 Jeopardy Web - Escuela Superior de Guerra

Sistema de preguntas y respuestas estilo Jeopardy para competencias entre equipos, completamente funcional en entorno local.

## 🚀 Inicio Rápido

### 1️⃣ Instalación

```bash
# Clonar o descargar el proyecto
cd jeopardy-web

# Instalar dependencias
pip install -r requirements.txt
```

### 2️⃣ Estructura de Archivos

Asegúrate de tener esta estructura:

```
jeopardy-web/
├── app.py
├── game_logic.py
├── requirements.txt
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── game.js
│   └── sounds/          # ← Coloca tus archivos de audio aquí
│       ├── boton_presionado2.wav
│       ├── aplausos.wav
│       ├── incorrecto.wav
│       └── contestando.wav
├── templates/
│   └── index.html
└── data/
    ├── preguntas.csv    # Opcional: tu banco de preguntas
    ├── usadas.csv       # Se crea automáticamente
    └── questions.json   # Opcional: formato JSON
```

### 3️⃣ Ejecutar el Servidor

```bash
python app.py
```

Verás algo como:

```
==================================================
🎮 JEOPARDY WEB - Servidor Iniciado
==================================================
📍 URL: http://localhost:5000
📍 Red local: http://192.168.1.X:5000

🎯 Controles:
   - Teclado 1-5: Buzzers de equipos
   - Teclado A-D: Seleccionar respuestas
   - Enter: Confirmar respuesta
   - Escape: Cancelar

⚡ WebSockets activos para tiempo real
==================================================
```

### 4️⃣ Acceder al Juego

- **En la misma PC**: http://localhost:5000
- **Desde otra PC/tablet/móvil en la red local**: http://[IP-del-servidor]:5000
  - Ejemplo: http://192.168.1.100:5000

---

## 🎯 Características

### ✅ Implementadas

- ✅ **5 equipos** con buzzers independientes
- ✅ **Temporizador** de 10 segundos con cuenta regresiva
- ✅ **Sistema de rebote**: Si un equipo falla, otros pueden intentar
- ✅ **Modo moderador**: Ocultar respuestas para validación manual
- ✅ **Efectos de sonido** para eventos del juego
- ✅ **Atajos de teclado** (1-5 buzzers, A-D respuestas, Enter/Esc)
- ✅ **Gestión de puntajes**: Ajuste manual con menú contextual (clic derecho)
- ✅ **Carga de preguntas**: JSON o CSV con sistema de "usadas"
- ✅ **Tiempo real**: WebSockets para sincronización instantánea
- ✅ **Responsive**: Funciona en desktop, tablets y móviles

### 🎨 Mejoras sobre Tkinter

1. **Multi-dispositivo**: Cada jugador puede usar su móvil como buzzer
2. **Sin instalación en clientes**: Solo necesitan un navegador
3. **Interfaz moderna**: Animaciones, transiciones suaves
4. **Accesible en red local**: Ideal para proyectar en TV/proyector
5. **Escalable**: Fácil agregar más equipos o funciones

---

## 🎮 Cómo Jugar

### Flujo del Juego

1. **Seleccionar pregunta**: Clic en una casilla del tablero
2. **Presionar buzzer**: Jugador presiona su botón (o tecla 1-5)
3. **Responder**: 
   - Si respuestas visibles: Seleccionar opción (A-D) y Enter
   - Si respuestas ocultas: Moderador valida con botones Correcto/Incorrecto
4. **Puntaje actualizado**: 
   - Correcto: +puntos de la pregunta
   - Incorrecto: -puntos + posibilidad de rebote
5. **Siguiente pregunta**: Repetir hasta terminar tablero

### Controles de Teclado

| Tecla | Acción |
|-------|--------|
| `1` - `5` | Buzzer de equipos |
| `A` - `D` | Seleccionar respuesta |
| `Enter` | Confirmar respuesta |
| `Escape` | Cancelar pregunta |

### Menú Contextual (Puntajes)

- **Clic derecho** sobre nombre de equipo para:
  - Sumar +100
  - Restar -100
  - Editar puntaje manualmente

---

## 📁 Formatos de Datos

### Opción 1: JSON

```json
{
  "categories": [
    {
      "name": "Ciencia",
      "clues": [
        {
          "value": 100,
          "question": "¿Cuál es el planeta más cercano al Sol?",
          "choices": ["Venus", "Mercurio", "Marte", "Tierra"],
          "answer": 1
        }
      ]
    }
  ]
}
```

### Opción 2: CSV

**Formato requerido** (`preguntas.csv`):

```csv
idpregunta,category,value,question,choice_a,choice_b,choice_c,choice_d,answer
1,Ciencia,100,¿Cuál es el planeta más cercano al Sol?,Venus,Mercurio,Marte,Tierra,b
2,Historia,200,¿En qué año llegó Colón a América?,1492,1519,1776,1453,a
```

**Campos:**
- `idpregunta`: ID único (entero)
- `category`: Categoría
- `value`: Puntos (100, 200, 300, 400, 500)
- `question`: Texto de la pregunta
- `choice_a`, `choice_b`, `choice_c`, `choice_d`: Opciones
- `answer`: Respuesta correcta (`a`, `b`, `c`, `d` o `0`, `1`, `2`, `3`)

### Sistema de "Preguntas Usadas"

El archivo `data/usadas.csv` se crea/actualiza automáticamente al cargar preguntas. Evita repetir preguntas entre rondas.

Para **nueva ronda con preguntas frescas**:
```python
# En game_logic.py ya está implementado
data = load_from_csv_sampled(
    "data/preguntas.csv",
    used_csv_path="data/usadas.csv"
)
```

Para **resetear preguntas usadas**:
```bash
# Simplemente borra el archivo
rm data/usadas.csv
```

---

## 🔧 Configuración Avanzada

### Cambiar Tiempo del Temporizador

En `game_logic.py`:
```python
TIME_LIMIT_SECONDS = 15  # Cambiar a 15 segundos
```

### Cambiar Número de Equipos

1. En `templates/index.html`: Agregar/quitar bloques `.player`
2. En `game_logic.py`: Ajustar `self.player_scores = [0, 0, 0, 0, 0, 0]` (6 equipos)

### Personalizar Sonidos

Reemplaza los archivos en `static/sounds/` con tus propios WAV:
- `boton_presionado2.wav`: Cuando alguien presiona buzzer
- `aplausos.wav`: Respuesta correcta
- `incorrecto.wav`: Respuesta incorrecta
- `contestando.wav`: Últimos 6 segundos del temporizador

### Cambiar Puerto del Servidor

En `app.py`:
```python
socketio.run(app, host='0.0.0.0', port=8080)  # Puerto 8080
```

---

## 🌐 Modo Multi-Pantalla (Avanzado)

### Configuración Dual

**Opción 1: Proyector + Tablet Moderador**
1. Proyector muestra: `http://localhost:5000` (vista principal)
2. Tablet moderador: `http://localhost:5000` con checkbox "Ocultar respuestas" activo

**Opción 2: Buzzers en Móviles**
1. Cada jugador abre la URL en su móvil
2. Solo usan los botones de buzzer
3. Proyector muestra el tablero central

---

## 🐛 Solución de Problemas

### Error: "Address already in use"
```bash
# Puerto 5000 ocupado, usar otro:
# Editar app.py línea final:
socketio.run(app, host='0.0.0.0', port=5001)
```

### Los sonidos no se reproducen
- Verifica que los archivos WAV existan en `static/sounds/`
- Algunos navegadores bloquean autoplay, haz clic en la página primero

### No se conecta desde otro dispositivo
- Verifica firewall del servidor
- Asegúrate de estar en la misma red WiFi
- Usa la IP correcta: `ipconfig` (Windows) o `ifconfig` (Linux/Mac)

### CSS/JS no cargan
```bash
# Limpiar caché del navegador: Ctrl+Shift+R
# O forzar recarga: Ctrl+F5
```

---

## 📝 TODO / Mejoras Futuras

- [ ] Subida de archivos CSV/JSON desde la interfaz
- [ ] Modo de práctica individual
- [ ] Estadísticas por equipo (% aciertos, tiempo promedio)
- [ ] Exportar resultados a PDF
- [ ] Temas visuales personalizables
- [ ] Modo "Daily Double" (apuestas)
- [ ] Soporte para imágenes en preguntas
- [ ] Panel de administración separado
- [ ] Historial de partidas
- [ ] Integración con Google Sheets

---

## 🤝 Contribuir

Para agregar funciones o reportar bugs:
1. Fork del proyecto
2. Crear rama: `git checkout -b feature/nueva-funcion`
3. Commit: `git commit -m "Agrega nueva función"`
4. Push: `git push origin feature/nueva-funcion`
5. Pull Request

---

## 📄 Licencia

Este proyecto está bajo licencia MIT. Úsalo libremente para educación y competencias.

---

## 🎓 Créditos

**Desarrollado para**: Escuela Superior de Guerra  
**Basado en**: Sistema Tkinter original  
**Tecnologías**: Flask, Socket.IO, JavaScript ES6, CSS3

---

## 📞 Soporte

Para dudas o problemas:
- Revisa la sección "Solución de Problemas"
- Verifica los logs del servidor en la terminal
- Abre un issue en el repositorio

**¡Que gane el mejor equipo! 🏆**
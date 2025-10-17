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
🖼️ Soporte para Imágenes en Preguntas
Estructura de Archivos
Para usar imágenes en tus preguntas, debes seguir esta estructura:
jeopardy-web/
├── data/
│   ├── preguntas.csv              # Tu archivo CSV de preguntas
│   ├── preguntas/                 # Carpeta con el MISMO nombre que el CSV
│   │   ├── mexico.jpg            # Tus imágenes
│   │   ├── europa.png
│   │   ├── bolivar.jpg
│   │   └── ...
│   └── usadas.csv
Regla importante: La carpeta de imágenes DEBE tener el mismo nombre que tu archivo CSV (sin la extensión).
Formato CSV con Imágenes
Tu archivo CSV debe incluir dos columnas adicionales:
CampoDescripciónValoresimagenIndica si la pregunta tiene imagensi o nonombre_imagenNombre del archivo de imagenejemplo.jpg, foto.png, etc.
Ejemplo de CSV:
csvidpregunta,category,value,question,choice_a,choice_b,choice_c,choice_d,answer,imagen,nombre_imagen
1,Geografía,100,¿Qué país se muestra?,México,Brasil,Argentina,Chile,a,si,mexico.jpg
2,Historia,100,¿Quién es este personaje?,Bolívar,San Martín,Hidalgo,Juárez,a,si,bolivar.png
3,Ciencia,200,¿Qué es la fotosíntesis?,Proceso A,Proceso B,Proceso C,Proceso D,c,no,
Formatos de Imagen Soportados

✅ JPG / JPEG
✅ PNG
✅ GIF
✅ WebP
✅ SVG

Comportamiento Visual
Modo Normal (Respuestas Visibles)
Cuando la pregunta tiene imagen y las respuestas están visibles:

La imagen se muestra a la izquierda
Las opciones de respuesta se muestran a la derecha
Layout lado a lado (responsive en móviles)

┌─────────────────────────────────┐
│  [IMAGEN]  │  a) Opción A       │
│            │  b) Opción B       │
│            │  c) Opción C       │
│            │  d) Opción D       │
└─────────────────────────────────┘
Modo Moderador (Respuestas Ocultas)
Cuando la pregunta tiene imagen y las respuestas están ocultas:

La imagen se muestra centrada
Ocupa todo el ancho disponible
No se muestran las opciones

┌─────────────────────────────────┐
│                                 │
│         [IMAGEN GRANDE]         │
│                                 │
└─────────────────────────────────┘
Tamaños Recomendados
Para mejor visualización:

Ancho: 800-1200px
Alto: 600-800px
Relación de aspecto: 4:3 o 16:9
Peso: < 500KB por imagen

Ejemplo Completo
1. Crear archivo CSV
Archivo: data/geografia.csv
csvidpregunta,category,value,question,choice_a,choice_b,choice_c,choice_d,answer,imagen,nombre_imagen
1,Países,100,¿Qué país es este?,México,Brasil,Argentina,Chile,a,si,pais1.jpg
2,Capitales,200,¿Cuál es la capital?,París,Londres,Madrid,Roma,a,si,ciudad1.jpg
2. Crear carpeta de imágenes
Crear carpeta: data/geografia/
3. Agregar imágenes
data/geografia/
├── pais1.jpg
└── ciudad1.jpg
4. Cargar en el juego

Abrir Jeopardy Web
Clic en "📂 Cargar"
Seleccionar geografia.csv
✅ ¡Listo! Las imágenes se cargarán automáticamente

Solución de Problemas
❌ "Imagen no disponible"
Causas posibles:

La carpeta no tiene el mismo nombre que el CSV
El nombre del archivo en nombre_imagen no coincide
La imagen no está en la carpeta correcta
Problema de permisos de lectura

Solución:
bash# Verificar estructura
ls -la data/
ls -la data/tu_archivo/

# Verificar nombres de archivos
# Asegúrate que coincidan exactamente (mayúsculas/minúsculas)
⚠️ "Carpeta de imágenes no encontrada"
Esto aparecerá en la consola del servidor si la carpeta no existe.
Solución:
bash# Crear la carpeta con el nombre correcto
mkdir data/nombre_de_tu_csv
🐌 Imágenes muy lentas
Solución:

Optimiza el tamaño de tus imágenes
Usa herramientas como TinyPNG o ImageOptim
Convierte a WebP para mejor compresión

bash# Ejemplo con imagemagick
convert original.jpg -quality 85 -resize 1200x optimizada.jpg
Consejos de Uso
✅ Buenas Prácticas

Usa nombres descriptivos: mapa_mexico.jpg en vez de img1.jpg
Mantén tamaños consistentes entre todas las imágenes
Usa fondos claros para mejor legibilidad
Prueba en modo móvil antes de la competencia

❌ Evitar

Nombres con espacios: mi imagen.jpg ❌ → mi_imagen.jpg ✅
Caracteres especiales: país#1.jpg ❌ → pais_1.jpg ✅
Imágenes muy pesadas (>1MB)
Resoluciones muy altas innecesarias

Migrar Preguntas Existentes
Si ya tienes un CSV sin las columnas de imagen, puedes agregarlas fácilmente:
Opción 1: Excel/LibreOffice

Abre tu CSV existente
Agrega dos columnas al final:

Columna imagen
Columna nombre_imagen


Para preguntas sin imagen, pon no en imagen y deja vacío nombre_imagen
Para preguntas con imagen, pon si en imagen y el nombre del archivo en nombre_imagen
Guarda como CSV

Opción 2: Script Python
pythonimport csv

# Leer CSV existente
with open('preguntas_antiguas.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Agregar columnas nuevas
for row in rows:
    row['imagen'] = 'no'
    row['nombre_imagen'] = ''

# Guardar nuevo CSV
fieldnames = list(rows[0].keys())
with open('preguntas_nuevas.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("✅ CSV migrado exitosamente")
Casos de Uso
1. Geografía Visual
Pregunta: ¿Qué país es este?

Mostrar mapa o bandera
Opciones: México, Brasil, Argentina, Chile

2. Historia con Personajes
Pregunta: ¿Quién es este personaje histórico?

Mostrar foto o retrato
Opciones: Nombres de personas

3. Ciencia con Diagramas
Pregunta: ¿Qué órgano es este?

Mostrar diagrama anatómico
Opciones: Corazón, Pulmón, Hígado, Riñón

4. Arte y Cultura
Pregunta: ¿Quién pintó esta obra?

Mostrar pintura famosa
Opciones: Nombres de artistas

5. Identificación Visual
Pregunta: ¿Qué edificio emblemático es este?

Mostrar foto de monumento
Opciones: Torre Eiffel, Coliseo, Taj Mahal, etc.

Ejemplo Completo Paso a Paso
Paso 1: Preparar el CSV
Crear data/historia_visual.csv:
csvidpregunta,category,value,question,choice_a,choice_b,choice_c,choice_d,answer,imagen,nombre_imagen
1,Personajes,100,¿Quién es este libertador?,Simón Bolívar,José de San Martín,Miguel Hidalgo,Benito Juárez,a,si,bolivar.jpg
2,Personajes,200,¿Quién es este presidente?,Abraham Lincoln,George Washington,Thomas Jefferson,Theodore Roosevelt,a,si,lincoln.jpg
3,Batallas,300,¿Qué batalla representa esta imagen?,Waterloo,Gettysburg,Stalingrado,Normandía,c,si,stalingrado.jpg
4,Personajes,400,¿Quién es este científico?,Albert Einstein,Isaac Newton,Galileo Galilei,Stephen Hawking,a,si,einstein.jpg
Paso 2: Crear la carpeta
bashmkdir data/historia_visual
Paso 3: Agregar las imágenes
Copiar o descargar las imágenes a la carpeta:
bashdata/historia_visual/
├── bolivar.jpg
├── lincoln.jpg
├── stalingrado.jpg
└── einstein.jpg
Paso 4: Verificar estructura
bash# Verificar que todo esté correcto
ls -l data/historia_visual.csv
ls -l data/historia_visual/

# Deberías ver:
# historia_visual.csv
# historia_visual/
#   ├── bolivar.jpg
#   ├── lincoln.jpg
#   ├── stalingrado.jpg
#   └── einstein.jpg
Paso 5: Cargar en el juego

Iniciar el servidor: python app.py
Abrir navegador: http://localhost:5000
Clic en "📂 Cargar"
Seleccionar historia_visual.csv
Verificar mensaje: "Datos cargados correctamente desde historia_visual.csv (con imágenes de historia_visual/)"

Paso 6: ¡Jugar!
Las preguntas con imagen mostrarán automáticamente las imágenes junto a las opciones.
Preguntas Frecuentes
¿Puedo mezclar preguntas con y sin imagen en el mismo CSV?
Sí, perfectamente. Solo marca imagen=si para las que tienen imagen y imagen=no para las que no.
¿Las imágenes se cargan desde internet?
No, todas las imágenes deben estar en tu carpeta local data/<nombre_csv>/. Esto garantiza que funcione sin conexión a internet.
¿Qué pasa si la imagen no se encuentra?
Se mostrará un mensaje "⚠️ Imagen no disponible" pero la pregunta seguirá siendo jugable con las opciones de texto.
¿Puedo usar GIFs animados?
Sí, los GIFs funcionan perfectamente. Solo recuerda mantenerlos ligeros (<500KB).
¿Las imágenes se ven en todos los dispositivos?
Sí, el diseño es responsive. En pantallas grandes se muestra lado a lado, en móviles se apila verticalmente.
¿Cómo optimizo muchas imágenes a la vez?
bash# Con imagemagick (Linux/Mac)
for img in *.jpg; do
    convert "$img" -quality 85 -resize 1200x "optimizada_$img"
done

# Con Python (todas las plataformas)
pip install Pillow
python -c "
from PIL import Image
import os
for f in os.listdir('.'):
    if f.endswith(('.jpg', '.png')):
        img = Image.open(f)
        img.thumbnail((1200, 800))
        img.save(f'opt_{f}', optimize=True, quality=85)
"
Soporte Técnico
Si tienes problemas:

Verifica la consola del servidor (terminal donde ejecutas python app.py)
Verifica la consola del navegador (F12 → Console)
Comprueba que los nombres de archivos coincidan exactamente
Revisa los permisos de lectura de las carpetas

Logs útiles en la consola del servidor:
📁 Carpeta de imágenes configurada: data/historia_visual
⚠️ No se encontró carpeta de imágenes: data/historia_visual
Error sirviendo imagen historia_visual/imagen.jpg: [descripción del error]

¡Ahora tus preguntas pueden ser mucho más visuales e interactivas! 🎨📸

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
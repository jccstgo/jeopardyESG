#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, csv
import os, sys
import time, math, random, hashlib
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path 

#-------------------------------------------------
try:
    import winsound
    _HAS_WINSOUND = True
except Exception:
    _HAS_WINSOUND = False

class Sounder:
    def __init__(self, buzz=None, ok=None, bad=None, contestando=None):
        self.files = {"buzz": buzz, "ok": ok, "bad": bad, "contestando": contestando}
        # Fallback si no hay winsound (Linux/Mac): intenta simpleaudio
        self._fallback = None
        self._playing = []  # guarda PlayObject de simpleaudio
        if not _HAS_WINSOUND:
            try:
                import simpleaudio  # pip install simpleaudio
                self._fallback = simpleaudio
            except Exception:
                self._fallback = None

    def set(self, key, path):
        self.files[key] = path

    def play(self, key, loop=False):
        path = self.files.get(key)
        if not path or not os.path.isfile(path):
            return
        # (Opcional) parar cualquier sonido antes de reproducir otro
        self.stop_all()

        if _HAS_WINSOUND and sys.platform.startswith("win"):
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC
            if loop:
                flags |= winsound.SND_LOOP
            try:
                winsound.PlaySound(path, flags)
            except Exception:
                pass
        elif self._fallback:
            try:
                wo = self._fallback.WaveObject.from_wave_file(path)
                po = wo.play()
                self._playing.append(po)
            except Exception:
                pass

    def stop_all(self):
        # Windows: purgar cualquier sonido winsound en reproducción asíncrona
        if _HAS_WINSOUND and sys.platform.startswith("win"):
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass
        # Fallback: detener todos los PlayObject activos
        if self._fallback and self._playing:
            for po in self._playing:
                try:
                    po.stop()
                except Exception:
                    pass
            self._playing.clear()

# --------------------------
# Configuración
# --------------------------
TIME_LIMIT_SECONDS = 10  # segundos de cuenta regresiva tras timbre

# --------------------------
# Dataset de respaldo
# --------------------------
SAMPLE_DATA: Dict[str, Any] = {
    "categories": [
        {
            "name": "Ciencia",
            "clues": [
                {"value": 100, "question": "¿Cuál es el planeta más cercano al Sol?", "choices": ["Venus", "Mercurio", "Marte", "Tierra"], "answer": 1},
                {"value": 200, "question": "¿Qué molécula transporta oxígeno en la sangre?", "choices": ["Insulina", "Hemoglobina", "Glucosa", "Colágeno"], "answer": 1},
                {"value": 300, "question": "¿Qué partícula tiene carga negativa?", "choices": ["Protón", "Neutrón", "Electrón", "Positrón"], "answer": 2},
                {"value": 400, "question": "¿Qué gas es esencial para la respiración humana", "choices": ["Oxígeno","Dióxido de carbono","Nitrógeno","1945"],"Hidrógeno": 0},
            ],
        },
        {
            "name": "Historia",
            "clues": [
                {"value": 100, "question": "¿En qué año llegó Cristóbal Colón a América?", "choices": ["1492", "1519", "1776", "1453"], "answer": 0},
                {"value": 200, "question": "¿Qué civilización construyó Machu Picchu?", "choices": ["Azteca", "Maya", "Inca", "Olmeca"], "answer": 2},
                {"value": 300, "question": "¿Quién fue conocido como el Libertador de América?", "choices": ["Simón Bolívar", "José de San Martín", "Miguel Hidalgo", "Bernardo O'Higgins"], "answer": 0},
                {"value": 400, "question": "¿En qué año comenzó la Segunda Guerra Mundial?", "choices": ["1935","1939","1941","1945"],"answer": 1},
            ],
        },
        {
            "name": "Tecnología",
            "clues": [
                {"value": 100, "question": "¿Qué significa 'CPU'?", "choices": ["Central Processing Unit", "Computer Personal Unit", "Core Processing Utility", "Central Peripheral Unit"], "answer": 0},
                {"value": 200, "question": "¿Qué protocolo se usa típicamente para la web?", "choices": ["FTP", "SMTP", "HTTP", "SSH"], "answer": 2},
                {"value": 300, "question": "¿Cuál de estos es un lenguaje de programación?", "choices": ["HTML", "CSS", "Python", "JSON"], "answer": 2},
                {"value": 400, "question": "¿Que protocolo nos permite navegar seguros en la web?", "choices": ["HTTP","HTTPS","FTP","TELNET"],"answer": 1},
            ],
        },
        {
            "name": "Geografía",
            "clues": [
                {"value": 100,"question": "¿Cuál es el río más largo del mundo?","choices": ["Amazonas","Nilo","Yangtsé","Misisipi"],"answer": 0},
                {"value": 200,"question": "¿En qué continente está Egipto?","choices": ["Asia","África","Europa","Oceanía"],"answer": 1},
                {"value": 300,"question": "¿Cuál es la capital de Japón?","choices": ["Pekín","Seúl","Tokio","Osaka"],"answer": 2},
                {"value": 400,"question": "¿Qué país tiene forma de bota?","choices": ["Grecia","Italia","España","Portugal"],"answer": 1},
            ],
        }
    ]
}


# ----------------------------------------------
# Utilidades para crear el archivo de usadas.csv
# ----------------------------------------------
def _row_id(category: str, value: int, question: str, choices: list) -> str:
    """Crea un ID estable para una fila de CSV (category, value, question, choices)."""
    txt = f"{category}|{value}|{question}|{'||'.join(choices)}"
    return hashlib.sha1(txt.encode("utf-8")).hexdigest()

def _read_used_ids(used_csv_path: str) -> Set[int]:
    """Lee usadas.csv y devuelve conjunto de idpregunta (enteros) ya utilizados."""
    used: Set[int] = set()
    p = Path(used_csv_path)
    if not p.exists():
        return used
    with p.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        # Admitimos 'idpregunta' (nuevo). Si no está, tratamos de leer 'id' por compatibilidad.
        for row in r:
            raw = (row.get("idpregunta") or row.get("id") or "").strip()
            if raw:
                try:
                    used.add(int(raw))
                except ValueError:
                    pass
    return used

def _append_used_rows(used_csv_path: str, rows: List[dict]):
    """
    Anexa filas a usadas.csv con encabezado basado en idpregunta.
    'rows' debe traer al menos: idpregunta, category, value, question, choice_a..d, answer
    """
    p = Path(used_csv_path)
    exists = p.exists()
    with p.open("a", encoding="utf-8", newline="") as f:
        fieldnames = ["idpregunta","category","value","question","choice_a","choice_b","choice_c","choice_d","answer"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            w.writeheader()
        for row in rows:
            w.writerow({
                "idpregunta": row.get("idpregunta"),
                "category": row.get("category",""),
                "value": row.get("value",0),
                "question": row.get("question",""),
                "choice_a": (row.get("choices",[ "", "", "", ""])[0] if "choices" in row else row.get("choice_a","")),
                "choice_b": (row.get("choices",[ "", "", "", ""])[1] if "choices" in row else row.get("choice_b","")),
                "choice_c": (row.get("choices",[ "", "", "", ""])[2] if "choices" in row else row.get("choice_c","")),
                "choice_d": (row.get("choices",[ "", "", "", ""])[3] if "choices" in row else row.get("choice_d","")),
                "answer":   row.get("answer",0),
            })

# --------------------------
# Carga de datos
# --------------------------

def load_data(path: str = "questions.json") -> Dict[str, Any]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "categories" not in data:
                raise ValueError("Formato JSON inválido: falta 'categories'.")
            return data
        except Exception:
            # En caso de error, usar dataset de ejemplo
            return SAMPLE_DATA
    return SAMPLE_DATA

#-----------------------------
# Carga datos desde un csv
#-----------------------------
def load_from_csv(path: str) -> dict:
    categories = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # empieza en 2 por el header
            cat = (row.get("category") or "General").strip()
            try:
                value = int(str(row.get("value", "0")).strip())
            except ValueError:
                value = 0

            question = (row.get("question") or "").strip()
            choices = [
                (row.get("choice_a") or "").strip(),
                (row.get("choice_b") or "").strip(),
                (row.get("choice_c") or "").strip(),
                (row.get("choice_d") or "").strip(),
            ]

            ans_raw = str(row.get("answer", "")).strip().lower()
            if ans_raw in ("a", "b", "c", "d"):
                answer = "abcd".index(ans_raw)
            else:
                # Permite 0/1/2/3
                try:
                    answer = int(ans_raw)
                except ValueError:
                    answer = 0  # por defecto

            categories.setdefault(cat, []).append({
                "value": value,
                "question": question,
                "choices": choices,
                "answer": answer
            })

    # Ordena las preguntas por valor dentro de cada categoría (opcional pero útil)
    cat_list = []
    for name, clues in categories.items():
        clues.sort(key=lambda d: d.get("value", 0))
        cat_list.append({"name": name, "clues": clues})

    return {"categories": cat_list}


#---------------------------------------------------
# Carga datos desde un csv muestreado aleatoriamente
#---------------------------------------------------

def load_from_csv_sampled(
    path: str,
    used_csv_path: str = "usadas.csv",
    values_per_category = (100, 200, 300, 400, 500),
    rng_seed: Optional[int] = None
) -> dict:
    """
    Lee un CSV y construye el dataset del juego seleccionando aleatoriamente UNA pregunta
    por cada (categoría, valor), excluyendo las ya presentes en usadas.csv por idpregunta.
    Los elegidos se agregan a usadas.csv.
    """
    import random
    if rng_seed is not None:
        random.seed(rng_seed)

    used_ids = _read_used_ids(used_csv_path)

    # Agrupamos por (cat, val)
    bucket: Dict[Tuple[str,int], List[dict]] = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # idpregunta (entero)
            try:
                qid = int(str(row.get("idpregunta","")).strip())
            except ValueError:
                continue

            cat = (row.get("category") or "General").strip()
            try:
                val = int(str(row.get("value","0")).strip())
            except ValueError:
                continue

            question = (row.get("question") or "").strip()
            choices = [
                (row.get("choice_a") or "").strip(),
                (row.get("choice_b") or "").strip(),
                (row.get("choice_c") or "").strip(),
                (row.get("choice_d") or "").strip(),
            ]
            ans_raw = str(row.get("answer","")).strip().lower()
            if ans_raw in ("a","b","c","d"):
                answer = "abcd".index(ans_raw)
            else:
                try: answer = int(ans_raw)
                except: answer = 0

            bucket.setdefault((cat, val), []).append({
                "idpregunta": qid,
                "category": cat,
                "value": val,
                "question": question,
                "choices": choices,
                "answer": answer,
            })

    categories: Dict[str, dict] = {}
    cats_in_csv = sorted({cat for (cat, _) in bucket.keys()})
    used_rows_to_append: List[dict] = []

    for cat in cats_in_csv:
        clues = []
        for val in values_per_category:
            pool = bucket.get((cat, val), [])
            # Filtra no usados por idpregunta
            fresh = [r for r in pool if r["idpregunta"] not in used_ids]

            if fresh:
                pick = random.choice(fresh)
            elif pool:
                # si no quedan frescos, fallback: reusar (o podrías dejar placeholder)
                #pick = random.choice(pool)
                #Si queremos que avise que ya no hay nuevas
                raise ValueError("No hay suficientes preguntas para otra ronda")
            else:
                # sin preguntas para esta casilla
                pick = {
                    "idpregunta": None,
                    "category": cat,
                    "value": val,
                    "question": f"(Sin pregunta disponible para {cat} {val})",
                    "choices": ["","","",""],
                    "answer": 0,
                    "unavailable": True
                }

            clues.append({
                "value": pick["value"],
                "question": pick["question"],
                "choices": pick["choices"],
                "answer": pick["answer"],
                **({"unavailable": True} if pick.get("unavailable") else {})
            })

            # Registrar en usadas SI tenía contenido real (y no placeholder)
            if not pick.get("unavailable") and any(pick["choices"]) and pick.get("idpregunta") is not None:
                used_rows_to_append.append({
                    "idpregunta": pick["idpregunta"],
                    "category": pick["category"],
                    "value": pick["value"],
                    "question": pick["question"],
                    "choices": pick["choices"],
                    "answer": pick["answer"],
                })
                used_ids.add(pick["idpregunta"])

        categories[cat] = {"name": cat, "clues": clues}

    if used_rows_to_append:
        _append_used_rows(used_csv_path, used_rows_to_append)

    return {"categories": [categories[c] for c in sorted(categories.keys())]}


'''
elif pool:
                # fallback: usar una usada si no hay nuevas
                pick = random.choice(pool)
                #Si queremos que avise que ya no hay nuevas
                #raise ValueError("No hay suficientes preguntas para otra ronda")
'''

def load_from_csv_strict_no_reuse(
    path: str,
    used_csv_path: str = "usadas.csv",
    values_per_category = (100, 200, 300, 400, 500),
) -> dict:
    """
    Construye el dataset eligiendo SOLO preguntas NO usadas (por idpregunta).
    Si falta alguna (cat,val) inserta placeholder {"unavailable": True}.
    No escribe en usadas.csv: se asume que lo harás al usarlas (o puedes mantener la escritura al construir, según tu flujo).
    """
    used_ids = _read_used_ids(used_csv_path)

    bucket: Dict[Tuple[str,int], List[dict]] = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                qid = int(str(row.get("idpregunta","")).strip())
            except ValueError:
                continue
            cat = (row.get("category") or "General").strip()
            try:
                val = int(str(row.get("value","0")).strip())
            except ValueError:
                continue

            # descarta usadas
            if qid in used_ids:
                continue

            q = (row.get("question") or "").strip()
            choices = [
                (row.get("choice_a") or "").strip(),
                (row.get("choice_b") or "").strip(),
                (row.get("choice_c") or "").strip(),
                (row.get("choice_d") or "").strip(),
            ]
            ans_raw = str(row.get("answer","")).strip().lower()
            if ans_raw in ("a","b","c","d"):
                ans = "abcd".index(ans_raw)
            else:
                try: ans = int(ans_raw)
                except: ans = 0

            bucket.setdefault((cat, val), []).append({
                "idpregunta": qid,
                "category": cat,
                "value": val,
                "question": q,
                "choices": choices,
                "answer": ans,
            })

    categories: Dict[str, dict] = {}
    cats = sorted({cat for (cat, _) in bucket.keys()})
    for cat in cats:
        clues = []
        for val in values_per_category:
            pool = bucket.get((cat, val), [])
            if pool:
                pick = pool[0]  # o random.choice(pool)
                clues.append({
                    "value": pick["value"],
                    "question": pick["question"],
                    "choices": pick["choices"],
                    "answer": pick["answer"],
                })
            else:
                clues.append({"value": val, "unavailable": True})
        categories[cat] = {"name": cat, "clues": clues}

    return {"categories": [categories[c] for c in sorted(categories.keys())]}


# --------------------------
# Aplicación principal
# --------------------------
class JeopardyApp(tk.Tk):
    def __init__(self, data: Dict[str, Any]):
        super().__init__()
        self.title("Escuela Superior de Guerra-Painani del conocimiento")

        # --- Ventana fija (no maximizable) y centrada ---
        win_w, win_h = 1080, 720
        self.geometry(f"{win_w}x{win_h}")
        #self.resizable(False, False)
        self.minsize(1080, 720)
        self.update_idletasks()
        scr_w = self.winfo_screenwidth()
        scr_h = self.winfo_screenheight()
        pos_x = (scr_w - win_w) // 2
        pos_y = (scr_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        self.configure(bg="white")
        #---------------------------------------------

        # Estado
        self.data = data
        self.used: Set[Tuple[int, int]] = set()  # (cat_idx, clue_idx)
        self.tile_status: Dict[Tuple[int, int], str] = {}  # 'correct' | 'used'
        self.player_scores = [0, 0, 0, 0, 0]
        self.current_buzzer: Optional[int] = None
        self.board_enabled = True  # Se elige pregunta primero
        self.current_question_panel: Optional["QuestionPanel"] = None
        self.tried_players: Set[int] = set()  # Jugadores que ya intentaron en la pregunta actual

        # Temporizador global (junto a timbres)
        self.timer_running = False
        self.timer_job: Optional[str] = None
        self.timer_end_ts: Optional[float] = None
        self.time_left = TIME_LIMIT_SECONDS

        # Estado de barra de estado / animación
        self.last_info_text: str = ""
        self._status_flash_job: Optional[str] = None
        self._status_revert_job: Optional[str] = None

        # Preferencia: ocultar respuestas
        self.hide_answers = tk.BooleanVar(value=False)

        # Estilos + Layout
        self._setup_style()
        self._build_layout()
        self.build_board()
        # Al inicio los timbres están deshabilitados hasta que se abra una pregunta
        self.enable_buzzers(False)
        # Atajos de teclado
        self._setup_keybindings()

        # === Sonidos del juego ===
        self.snd = Sounder(
            buzz="sonidos/boton_presionado2.wav",        # suena cuando alguien pide turno
            ok="sonidos/aplausos.wav",       # respuesta correcta
            bad="sonidos/incorrecto.wav",     # respuesta incorrecta
            #contestando="sonidos/ultsegundos.wav"
            contestando="sonidos/contestando.wav"

        )

    # ---------------------- Estilos ----------------------
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("White.TFrame", background="white")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), background="white")
        style.configure("Cat.TLabel", font=("Segoe UI", 12, "bold"), anchor="center", background="white")
        # Estilo grande para encabezados de categorías
        style.configure("CatHeader.TLabel", font=("Segoe UI", 20, "bold"), anchor="center", background="white")

    # ---------------------- Layout ----------------------
    def _build_layout(self):
        # Header
        self.header = ttk.Frame(self, padding=(10, 8), style="White.TFrame")
        self.header.pack(side=tk.TOP, fill=tk.X)

        # Barra de jugadores + temporizador al extremo derecho
        self.players_frame = ttk.Frame(self.header, style="White.TFrame")
        self.players_frame.pack(side=tk.TOP, fill=tk.X)
        self._build_players_bar()

        # Barra de estado centrada (azul cielo)
        self.status_var = tk.StringVar(value="Selecciona una casilla para abrir una pregunta.")
        self.status_label = tk.Label(
            self.header,
            textvariable=self.status_var,
            bg="#87CEEB",  # azul cielo
            fg="black",
            font=("Segoe UI", 12, "bold"),
            anchor="center",
            justify="center",
            padx=8, pady=6,
        )
        #------------------------------------------------
        self._build_score_menu()
        self.status_label.pack(side=tk.TOP, fill=tk.X, pady=(6, 0))
        self.set_status("Selecciona una casilla para abrir una pregunta.", "info")

        # Área central (tablero o panel de pregunta)
        self.center = ttk.Frame(self, style="White.TFrame")
        self.center.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.board = ttk.Frame(self.center, style="White.TFrame")
        self.board.pack(fill=tk.BOTH, expand=True)

        # Controles inferiores
        self.controls = ttk.Frame(self, padding=(10, 8), style="White.TFrame")
        self.controls.pack(side=tk.BOTTOM, fill=tk.X)
        # Botones por defecto (modo tablero)
        self.btn_exit = ttk.Button(self.controls, text="Salir", command=self.quit_app)
        self.btn_exit.pack(side=tk.RIGHT, padx=5)
        #-----------------------------------------------------------------------------
        #Boton nueva ronda
        #-----------------------------------------------------------------------------
        #self.btn_nueva_ronda = ttk.Button(self.controls, text="Nueva ronda", command=self.new_round)
        #self.btn_nueva_ronda.pack(side=tk.RIGHT, padx=5)
        self.btn_reset = ttk.Button(self.controls, text="Reiniciar", command=self.reset_game)
        self.btn_reset.pack(side=tk.RIGHT, padx=5)
        self.btn_load = ttk.Button(self.controls, text="Cargar", command=self.reload_json)
        self.btn_load.pack(side=tk.RIGHT)
        # Checkbox (sólo visible en tablero)
        self.hide_chk = ttk.Checkbutton(self.controls, text="Ocultar respuestas", variable=self.hide_answers, command=self.on_toggle_hide_answers)
        self.hide_chk.pack(side=tk.RIGHT, padx=(10, 0))

        # Botones de moderador (modo pregunta con respuestas ocultas)
        self.mod_cancel = ttk.Button(self.controls, text="Cancelar", command=lambda: self.current_question_panel and self.current_question_panel.cancel_turn())
        # Colores para Correcto/Incorrecto (usar tk.Button para fondo)
        self.mod_correct = tk.Button(self.controls, text="Correcto", command=lambda: self.current_question_panel and self.current_question_panel.moderator_correct(), bg="#28a745", fg="white", activebackground="#218838", activeforeground="white")
        self.mod_incorrect = tk.Button(self.controls, text="Incorrecto", command=lambda: self.current_question_panel and self.current_question_panel.moderator_incorrect(), bg="#CC0000", fg="white", activebackground="#AA0000", activeforeground="white")
        # Botones de panel visible (respuestas visibles): Responder/Cancelar en barra inferior
        self.panel_responder = ttk.Button(self.controls, text="Responder", command=lambda: self.current_question_panel and self.current_question_panel.submit())
        self.panel_cancel = ttk.Button(self.controls, text="Cancelar", command=lambda: self.current_question_panel and self.current_question_panel.cancel_turn())
        # Por defecto ocultos
        for w in (self.mod_incorrect, self.mod_correct, self.mod_cancel, self.panel_responder, self.panel_cancel):
            w.pack_forget()

    def _build_players_bar(self):  # crea contenedores de jugadores y timer
        for w in self.players_frame.winfo_children():
            w.destroy()

        self.player_btns: List[tk.Button] = []
        self.player_score_vars: List[tk.StringVar] = []

        # 5 columnas para jugadores + 1 columna para temporizador
        for i in range(5):
            col = ttk.Frame(self.players_frame, style="White.TFrame")
            col.grid(row=0, column=i, sticky="nsew", padx=6, pady=4)

            btn = tk.Button(
                col,
                text=f"Equipo {i+1}",
                font=("Segoe UI", 11, "bold"),
                bg="#90EE90",  # verde claro
                activebackground="#7EDC7E",
                fg="black",
                relief=tk.RAISED,
                cursor="hand2",
                command=lambda idx=i: self.on_buzzer(idx),
            )
            btn.pack(fill=tk.X)
            #self.player_btns.append(btn)

            #----------------------------------------------
            #menú contextual (clic derecho)
            btn.bind("<Button-3>", lambda e, n=i: self._open_score_menu(e, n))     # clic derecho
            self.player_btns.append(btn)
            var = tk.StringVar(value=f"Puntos: {self.player_scores[i]}")
            self.player_score_vars.append(var)
            ttk.Label(col, textvariable=var, style="Title.TLabel", anchor="center").pack(pady=(4, 0))

        # Columna de temporizador
        tcol = ttk.Frame(self.players_frame, style="White.TFrame")
        tcol.grid(row=0, column=5, sticky="nsew", padx=(12, 0), pady=4)
        ttk.Label(tcol, text="Tiempo", style="Title.TLabel").pack(anchor="e", pady=(0, 4))
        self.timer_label_var = tk.StringVar(value="—")
        self.timer_label = tk.Label(
            tcol,
            textvariable=self.timer_label_var,
            font=("Segoe UI", 22, "bold"),
            bg="black",
            fg="red",
            width=6,
            padx=10,
            pady=6,
        )
        self.timer_label.pack(anchor="e")

        for i in range(6):
            self.players_frame.columnconfigure(i, weight=1, uniform="players")

    # ---------------------- Barra de estado ----------------------
    def set_status(self, text: str, variant: str = "info"):
        """Actualiza la barra de estado. Variants: 'info' (negro, mediano),
        'correct' (verde grande, 'CORRECTO'), 'incorrect' (rojo grande, 'INCORRECTO')."""
        # Cancelar animaciones previas si las hubiera
        if self._status_flash_job is not None:
            try: self.after_cancel(self._status_flash_job)
            except Exception: pass
            self._status_flash_job = None
        if self._status_revert_job is not None:
            try: self.after_cancel(self._status_revert_job)
            except Exception: pass
            self._status_revert_job = None

        if variant == "correct":
            self.status_var.set("CORRECTO")
            self.status_label.configure(fg="green", font=("Segoe UI", 22, "bold"), bg="#87CEEB")
        elif variant == "incorrect":
            self.status_var.set("INCORRECTO")
            self.status_label.configure(fg="red", font=("Segoe UI", 22, "bold"), bg="#87CEEB")
        else:
            self.status_var.set(text)
            self.status_label.configure(fg="black", font=("Segoe UI", 12, "bold"), bg="#87CEEB")
            self.last_info_text = text

    def flash_status(self, variant: str, after_text: Optional[str] = None, flashes: int = 4, interval_ms: int = 120):
        """Hace parpadear la barra para 'correct' o 'incorrect' y luego vuelve a info."""
        self.set_status("", variant)
        target_color = "green" if variant == "correct" else "red"
        count = {"n": 0}
        def _blink():
            if count["n"] >= flashes:
                self.set_status(after_text or self.last_info_text or "", "info")
                return
            current = self.status_label.cget("fg")
            self.status_label.configure(fg=(target_color if current == "white" else "white"))
            count["n"] += 1
            self._status_flash_job = self.after(interval_ms, _blink)
        _blink()

    # ---------------------- Utilidades de UI ----------------------
    def update_player_button_colors(self):
        for i, b in enumerate(self.player_btns):
            if self.current_buzzer is None:
                b.configure(bg="#90EE90", activebackground="#7EDC7E", fg="black")
            else:
                if i == self.current_buzzer:
                    b.configure(bg="#CC0000", activebackground="#AA0000", fg="white")  # rojo
                else:
                    b.configure(bg="#90EE90", activebackground="#7EDC7E", fg="black")

    # ---------------------- Temporizador global ----------------------
    def start_timer(self):
        # Reinicia el temporizador usando tiempo absoluto para evitar saltos por bloqueos del mainloop
        if self.timer_running and self.timer_job is not None:
            try:
                self.after_cancel(self.timer_job)
            except Exception:
                pass
        self.timer_end_ts = time.perf_counter() + TIME_LIMIT_SECONDS
        self.timer_running = True
        #-------------------------Agregar sonido contador---------------------------
        #if hasattr(self, "snd"): self.snd.play("contestando")
        self.timer_job = self.after(50, self._tick_timer)

    def _tick_timer(self):
        if not self.timer_running or self.timer_end_ts is None:
            return
        remaining = max(0.0, self.timer_end_ts - time.perf_counter())
        self.time_left = int(math.ceil(remaining))
        self._update_timer_label()
        #---------------------------------------------------------------
        if self.time_left == 6:
            self.snd.play("contestando")
        #---------------------------------------------------------------
        if remaining <= 0.0 or self.time_left <= 0:
            self.timer_running = False
            self._update_timer_label()
            # Si hay selección hecha (teclado o mouse) y respuestas visibles, validar automáticamente
            if self.current_question_panel is not None and self.current_buzzer is not None:
                panel = self.current_question_panel
                if not self.hide_answers.get():
                    sel = panel.choice_var.get()
                    if sel >= 0:
                        # Evaluar como correcto/incorrecto
                        result = "correct" if sel == panel.answer_idx else "incorrect"
                        self.process_answer(panel.cat_idx, panel.clue_idx, result, panel.value, panel)
                        return
                # Si no había selección o están ocultas, tratar como timeout (incorrecto + rebote si procede)
                self.process_answer(panel.cat_idx, panel.clue_idx, "timeout", panel.value, panel)
            return
        self.timer_job = self.after(200, self._tick_timer)

    def stop_timer(self):
        if self.timer_job is not None:
            try:
                self.after_cancel(self.timer_job)
            except Exception:
                pass
        self.timer_running = False
        self.timer_job = None
        self.timer_end_ts = None
        self._update_timer_label()

    def _update_timer_label(self):
        self.timer_label_var.set(str(self.time_left) if self.timer_running else "—")

    # ---------------------- Estados de timbres/tablero ----------------------
    def on_buzzer(self, player_idx: int):
        # Sólo válido si hay una pregunta abierta, nadie con turno y el jugador no ha intentado antes
        if self.current_question_panel is None or self.current_buzzer is not None:
            return
        if player_idx in self.tried_players:
            return
        self.current_buzzer = player_idx
        #sound_buzzer()
        if hasattr(self, "snd"): self.snd.play("buzz")
        self.update_player_button_colors()
        self.set_status(f"Equipo {player_idx+1} tiene el turno. ¡Responde!", "info")
        # Deshabilita los otros timbres
        for i, b in enumerate(self.player_btns):
            if i != player_idx:
                b.configure(state=tk.DISABLED)
        # Inicia temporizador
        self.start_timer()
        # Habilitar opciones sólo si NO está oculto
        if self.current_question_panel is not None:
            self.current_question_panel.set_turn_text(f"Responde: Equipo {player_idx+1}")
            if not self.hide_answers.get():
                self.current_question_panel.enable_choices(True)
            else:
                self.current_question_panel.enable_choices(False)

    def enable_buzzers(self, enable: bool = True):
        if enable:
            for i, b in enumerate(self.player_btns):
                state = tk.NORMAL if i not in self.tried_players else tk.DISABLED
                b.configure(state=state)
            self.current_buzzer = None
            self.update_player_button_colors()
        else:
            for b in self.player_btns:
                b.configure(state=tk.DISABLED)
            self.current_buzzer = None
            self.update_player_button_colors()

    def set_board_enabled(self, enabled: bool):
        self.board_enabled = enabled
        self.build_board()

    # ---------------------- Tablero ----------------------
    def build_board(self):
        # Limpiar center y reconstruir board
        for w in self.center.winfo_children():
            w.destroy()
        self.board = ttk.Frame(self.center, style="White.TFrame")
        self.board.pack(fill=tk.BOTH, expand=True)

        categories: List[Dict[str, Any]] = self.data.get("categories", [])
        if not categories:
            ttk.Label(self.board, text="No hay categorías.", style="Cat.TLabel").pack()
            # Asegura que el checkbox sea visible en tablero
            self.set_hide_checkbox_visible(True)
            return
        max_clues = max((len(cat.get("clues", [])) for cat in categories), default=0)
        # Encabezados
        for c, cat in enumerate(categories):
            lbl = ttk.Label(
            self.board,
            text=cat.get("name", f"Cat {c+1}"),
            style="CatHeader.TLabel",
            wraplength=180,
            anchor="center",
            justify="center",
        )
            lbl.grid(row=0, column=c, sticky="nsew", padx=4, pady=4)
        # Celdas
        for r in range(1, max_clues + 1):
            for c, cat in enumerate(categories):
                clues = cat.get("clues", [])
                if r - 1 < len(clues):
                    clue = clues[r - 1]
                    value = clue.get("value", (r * 100))
                    text = f"{value}"
                    key = (c, r - 1)
                    status = self.tile_status.get(key)
                    # Estado y color
                    if status == 'correct':
                        state = tk.DISABLED
                        bg = "#87CEEB"  # azul cielo
                        fg = "black"
                    elif status == 'used':
                        state = tk.DISABLED
                        bg = "#87CEEB"  # azul cielo
                        fg = "red"      # letras rojas
                    else:
                        state = tk.NORMAL if (self.board_enabled and key not in self.used) else tk.DISABLED
                        bg = "#001f3f"
                        fg = "white"
                    btn = tk.Button(
                        self.board,
                        text=text,
                        font=("Segoe UI", 16, "bold"),
                        bg=bg, fg=fg,
                        activebackground="#12345a", activeforeground="white",
                        relief=tk.RAISED,
                        cursor="hand2" if state == tk.NORMAL else "arrow",
                        state=state,
                        command=lambda ci=c, ri=r - 1: self.on_tile_click(ci, ri),
                    )
                else:
                    btn = tk.Button(self.board, text="—", state=tk.DISABLED, bg="#dddddd")
                btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4, ipadx=8, ipady=14)
        for c in range(len(categories)):
            self.board.columnconfigure(c, weight=1, uniform="col")
        for r in range(max_clues + 1):
            self.board.rowconfigure(r, weight=1)
        # Asegura que el checkbox sea visible en tablero
        #self.set_hide_checkbox_visible(True)
        #----------Habilita menu contextual---------------
        self._activa_menu_contextual(True)   

    # ---------------------- Panel de pregunta embebido ----------------------
    def show_question_panel(self, cat_idx: int, clue_idx: int, clue: Dict[str, Any]):
        # Limpiar center y mostrar panel
        for w in self.center.winfo_children():
            w.destroy()
        panel = QuestionPanel(self.center, self, cat_idx, clue_idx, clue)
        panel.pack(fill=tk.BOTH, expand=True)
        #--------Desactiva menu contextual---------------
        self._activa_menu_contextual(False)
        self.current_question_panel = panel
        # Oculta el checkbox mientras está la pregunta embebida
        self.set_hide_checkbox_visible(False)
        # Controles según modo ocultar/visible
        if self.hide_answers.get():
            self.set_controls_mode('moderator')
        else:
            self.set_controls_mode('panel')
        # Respetar estado del checkbox (por si se activó antes de abrir)
        panel.apply_hide_state()

    # ---------------------- Mostrar/ocultar checkbox tablero ----------------------
    def set_hide_checkbox_visible(self, visible: bool):
        # Muestra el checkbox sólo en el tablero; lo oculta cuando hay pregunta embebida
        try:
            if visible:
                if self.hide_chk.winfo_manager() != 'pack':
                    self.hide_chk.pack(side=tk.RIGHT, padx=(10, 0))
            else:
                if self.hide_chk.winfo_manager() == 'pack':
                    self.hide_chk.pack_forget()
        except Exception:
            pass

    def set_controls_mode(self, mode: str):
        """'board' → muestra (Cargar/Reiniciar/Salir).
        'moderator' → muestra (Cancelar/Correcto/Incorrecto) y oculta los de tablero.
        'panel' → muestra (Responder/Cancelar) y oculta los de tablero.
        """
        # Ocultar todo inicialmente
        for w in (self.btn_exit, self.btn_reset, self.btn_load,
                  self.mod_incorrect, self.mod_correct, self.mod_cancel,
                  self.panel_responder, self.panel_cancel):
            if w.winfo_manager() == 'pack':
                w.pack_forget()
        if mode == 'moderator':
            # Mostrar botones del moderador (alineados a la derecha)
            self.mod_incorrect.pack(side=tk.RIGHT, padx=5)
            self.mod_correct.pack(side=tk.RIGHT, padx=5)
            self.mod_cancel.pack(side=tk.RIGHT, padx=5)
        elif mode == 'panel':
            # Mostrar botones Responder / Cancelar
            self.panel_responder.pack(side=tk.RIGHT, padx=5)
            self.panel_cancel.pack(side=tk.RIGHT, padx=5)
        else:
            # Modo tablero
            self.btn_exit.pack(side=tk.RIGHT, padx=5)
            self.btn_reset.pack(side=tk.RIGHT, padx=5)
            self.btn_load.pack(side=tk.RIGHT)

    # ---------------------- Flujo de pregunta ----------------------
    def on_tile_click(self, cat_idx: int, clue_idx: int):
        if (cat_idx, clue_idx) in self.used or not self.board_enabled:
            return
        cat = self.data["categories"][cat_idx]
        clue = cat["clues"][clue_idx]
        # Abrir pregunta: deshabilitar tablero y habilitar timbres (limpiando rebote previo)
        self.tried_players = set()
        self.set_board_enabled(False)
        self.enable_buzzers(True)
        self.set_status("Pregunta abierta. ¡Toca tu timbre para responder!", "info")
        self.show_question_panel(cat_idx, clue_idx, clue)

    def end_question_cleanup(self):
        # Cerrar panel si existe
        if self.current_question_panel and self.current_question_panel.winfo_exists():
            try:
                self.current_question_panel.destroy()
            except Exception:
                pass
        self.current_question_panel = None
        self.tried_players = set()
        # Detener temporizador y restaurar estados (siguiente turno)
        self.stop_timer()
        self.enable_buzzers(False)
        self.set_board_enabled(True)
        self.update_player_button_colors()
        # Restaurar controles y checkbox
        self.set_controls_mode('board')
        self.set_hide_checkbox_visible(True)
        # Re-render tablero para reflejar colores finales
        self.build_board()

    def remaining_players(self) -> List[int]:
        return [i for i in range(5) if i not in self.tried_players]

    def process_answer(self, cat_idx: int, clue_idx: int, result: str, value: int, panel: Optional["QuestionPanel"] = None) -> bool:
        """Procesa la respuesta del jugador actual.
        Retorna True si se debe CERRAR la pregunta (fin de turno), False si continúa (rebote).
        result ∈ {"correct", "incorrect", "timeout", "cancel"}
        """
        # Correcto: sumar, cerrar pregunta definitivamente
        if result == "correct":
            if self.current_buzzer is not None:
                self.player_scores[self.current_buzzer] += value
                #sound_correct()
                # 🔊 Sonido de correcto
                if hasattr(self, "snd"): self.snd.play("ok")
            # marcar usada como correcta y finalizar
            self.used.add((cat_idx, clue_idx))
            self.tile_status[(cat_idx, clue_idx)] = 'correct'
            self._refresh_scores()
            # Flash de CORRECTO y luego mensaje breve
            self.flash_status('correct', after_text="¡Correcto! Elige otra casilla.")
            self.end_question_cleanup()
            return True

        # Cancelar: no altera puntajes, cierra pregunta
        if result == "cancel":
            self.set_status("Turno cancelado. Elige otra casilla.", "info")
            self.end_question_cleanup()
            return True

        # Incorrecto o Timeout: penaliza al jugador actual y rebota si hay más jugadores
        if self.current_buzzer is not None:
            self.player_scores[self.current_buzzer] -= value
            #sound_incorrect()
            if hasattr(self, "snd"): self.snd.play("bad")
            self.tried_players.add(self.current_buzzer)
        self._refresh_scores()

        # ¿Quedan jugadores disponibles para intentar?
        remaining = self.remaining_players()
        if remaining:
            # Preparar siguiente intento: liberar turno, habilitar timbres disponibles, detener timer
            self.stop_timer()
            self.current_buzzer = None
            self.update_player_button_colors()
            for i, b in enumerate(self.player_btns):
                b.configure(state=(tk.NORMAL if i in remaining else tk.DISABLED))
            # Mantener panel abierto
            if self.current_question_panel is not None:
                self.current_question_panel.set_turn_text("Rebote: esperando otro equipo…")
                # Deshabilitar selección hasta nuevo timbre
                self.current_question_panel.enable_choices(False)
                # Limpiar selección anterior por si acaso
                self.current_question_panel.reset_selection()
            # Flash de INCORRECTO y luego mensaje de rebote
            self.flash_status('incorrect', after_text="Rebote: otro equipo puede contestar.")
            return False  # CONTINÚA

        # Si no quedan jugadores: cerrar pregunta, marcar como usada (no correcta)
        self.used.add((cat_idx, clue_idx))
        self.tile_status[(cat_idx, clue_idx)] = 'used'
        # Flash de INCORRECTO y luego mensaje de cierre
        self.flash_status('incorrect', after_text="Sin intentos restantes. Elige otra casilla.")
        self.end_question_cleanup()
        return True

    def _refresh_scores(self):
        for i, var in enumerate(self.player_score_vars):
            var.set(f"Puntos: {self.player_scores[i]}")

    # ---------------------- General ----------------------
    def on_toggle_hide_answers(self):
        # Refresca el panel actual (si existe) para mostrar/ocultar opciones y botones
        if self.current_question_panel and self.current_question_panel.winfo_exists():
            self.current_question_panel.apply_hide_state()
            # Cambiar modo de controles acorde al estado
            if self.hide_answers.get():
                self.set_controls_mode('moderator')
            else:
                self.set_controls_mode('panel')

    def new_round(self):
        """
        Carga una nueva ronda desde 'preguntas.csv' tomando SOLO preguntas NO usadas (usadas.csv).
        Si faltan preguntas para alguna (cat, val), esa casilla aparecerá como 'X' gris deshabilitada.
        """
        try:
            csv_path = "preguntas.csv"  # puedes volverlo seleccionable si quieres
            if not Path(csv_path).exists():
                messagebox.showerror("Error", f"No se encontró '{csv_path}'.")
                return
            self.data = load_from_csv_strict_no_reuse(
                csv_path,
                used_csv_path="usadas.csv",
                values_per_category=(100, 200, 300, 400, 500),
            )
            # Al iniciar una nueva ronda, limpiamos estado de casillas
            self.used.clear()
            self.tile_status.clear()
            # Salir del panel de pregunta (si abierto)
            for w in self.center.winfo_children():
                w.destroy()
            self.build_board()
            self.set_status("Nueva ronda cargada (solo preguntas NO usadas).")
            # Deshabilitar buzzers hasta abrir una pregunta
            self.enable_buzzers(False)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la nueva ronda:\n{e}")

    def reset_game(self):
        # Reinicia puntajes y tablero
        self.used.clear()
        self.tile_status.clear()
        self.player_scores = [0, 0, 0, 0, 0]
        self.tried_players = set()
        self._refresh_scores()
        self.current_buzzer = None
        self.stop_timer()
        self.enable_buzzers(False)
        self.set_board_enabled(True)
        self.build_board()
        self.set_status("Juego reiniciado. Selecciona una casilla para abrir pregunta.", "info")

    '''def reload_json(self):
        # Permitir seleccionar archivo JSON
        path = filedialog.askopenfilename(
            title="Selecciona archivo de preguntas",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        new_data = load_data(path)
        self.data = new_data

        # Reset de estado
        self.used.clear()
        self.tile_status.clear()
        self.tried_players = set()
        self.current_buzzer = None
        self.stop_timer()
        self.enable_buzzers(False)
        self.set_board_enabled(True)
        self.build_board()
        self.set_status("Datos recargados. Selecciona una casilla para abrir pregunta.", "info")'''

    def reload_json(self):
        path = filedialog.askopenfilename(
            title="Selecciona archivo de preguntas",
            filetypes=[
                ("JSON o CSV", "*.json *.csv"),
                ("Archivos JSON", "*.json"),
                ("Archivos CSV", "*.csv"),
                ("Todos", "*.*"),
            ],
        )
        if not path:
            return

        lower = path.lower()
        try:
            if lower.endswith(".csv"):
                #self.data = load_from_csv(path)
                self.data = load_from_csv_sampled(
                #self.data = load_from_csv_strict_no_reuse(
                    path,
                    used_csv_path="usadas.csv",
                    values_per_category=(100,200,300,400,500),  # ajusta si tu tablero usa otros
                    rng_seed=None  # o fija una semilla para reproducibilidad, p.ej. 1234
                )
            else:
                # Mantén tu función JSON existente (por ejemplo, load_data)
                new_data = load_data(path)
                self.data = new_data
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")
            return

        # Reinicia el tablero
        self.used.clear()
        if hasattr(self, "tile_status"):
            self.tile_status.clear()

        self.tried_players = set()
        self.current_buzzer = None
        self.stop_timer()
        self.enable_buzzers(False)
        self.set_board_enabled(True)
        self.build_board()
        self.set_status("Archivo cargado. Selecciona una casilla para abrir una pregunta.","info")


    def quit_app(self):
        try:
            if messagebox.askyesno("Salir", "¿Deseas salir del juego?"):
                try:
                    self.stop_timer()
                except Exception:
                    pass
                self.destroy()
        except Exception:
            # Si hubiese algún problema con messagebox, cerrar de todos modos
            try:
                self.destroy()
            except Exception:
                pass

    def main_loop(self):
        self.mainloop()

    # ---------------------- Atajos de teclado ----------------------
    def _setup_keybindings(self):
        # Números 1-5 para timbres de jugadores
        for n in range(1, 6):
            self.bind_all(str(n), lambda e, idx=n-1: self.on_buzzer(idx))
        # Letras a-d para seleccionar opciones (cuando están visibles y hay turno)
        letters = ['a', 'b', 'c', 'd']
        for i, ch in enumerate(letters):
            self.bind_all(ch, lambda e, idx=i: self._on_choice_letter(idx))
            self.bind_all(ch.upper(), lambda e, idx=i: self._on_choice_letter(idx))

    def _on_choice_letter(self, idx: int):
        # Sólo si hay panel, respuestas visibles y un jugador con turno
        if (self.current_question_panel is None
                or self.hide_answers.get()
                or self.current_buzzer is None):
            return
        panel = self.current_question_panel
        if 0 <= idx < len(panel.choice_rbs):
            # Seleccionar esa opción
            panel.choice_var.set(idx)
            # Opcional: feedback en la barra
            self.set_status(f"Opción seleccionada: {chr(97+idx)})", "info")

    #-------------------------------------------------------------------
    #----------------Metodos para la modificación del marcador----------
    def _build_score_menu(self):
        """Crea el menú contextual para ajustar marcadores."""
        self._menu_player = None
        self.score_menu = tk.Menu(self, tearoff=0)
        # Acciones fijas
        self.score_menu.add_command(label="Sumar +100", command=lambda: self._adjust_score(self._menu_player, +100))
        self.score_menu.add_command(label="Restar -100", command=lambda: self._adjust_score(self._menu_player, -100))
        self.score_menu.add_separator()
        # Acciones con valor de la pregunta (si hay pregunta abierta)
        #self.score_menu.add_command(label="Sumar valor de la pregunta", command=lambda: self._adjust_score_by_current_value(self._menu_player, +1))
        #self.score_menu.add_command(label="Restar valor de la pregunta", command=lambda: self._adjust_score_by_current_value(self._menu_player, -1))
        #self.score_menu.add_separator()
        # Editar directo
        self.score_menu.add_command(label="Editar…", command=lambda: self._edit_score(self._menu_player))

    def _open_score_menu(self, event, player_idx: int):
        """Muestra el menú contextual para el jugador indicado."""
        self._menu_player = player_idx
        try:
            self.score_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.score_menu.grab_release()

    def _adjust_score(self, player_idx: int, delta: int):
        """Suma/resta puntos al jugador indicado."""
        if not (0 <= player_idx < 5):
            return
        #self.player_scores[player_idx - 1] += delta
        self.player_scores[player_idx] += delta
        #self.update_scores_ui()
        self._refresh_scores()

    '''def _adjust_score_by_current_value(self, player_idx: int, sign: int):
        """Suma/resta el valor de la pregunta actual (si existe) al jugador."""
        if not (1 <= player_idx <= 5):
            return
        value = 0
        # Si hay un panel de pregunta abierto, tomar su 'value'
        if hasattr(self, "question_panel") and self.question_panel:
            try:
                value = int(self.question_panel.value)
            except Exception:
                value = 0
        if value == 0:
            # Si no hay pregunta activa, usa 100 por defecto (o cámbialo a lo que prefieras)
            value = 100
        self._adjust_score(player_idx, sign * value)'''

    def _edit_score(self, player_idx: int):
        """Permite escribir manualmente el puntaje del jugador."""
        if not (0 <= player_idx < 5):
            return
        #actual = self.player_scores[player_idx - 1]
        actual = self.player_scores[player_idx]
        nuevo = simpledialog.askinteger(
            "Editar marcador",
            f"Ingrese el nuevo puntaje para el equipo {player_idx + 1}:",
            initialvalue=actual,
            parent=self
        )
        if nuevo is not None:
            #self.player_scores[player_idx - 1] = int(nuevo)
            self.player_scores[player_idx] = int(nuevo)
            #self.update_scores_ui()
            self._refresh_scores()

    #-----Activa/Desactiva menu contextual---------------------
    def _activa_menu_contextual(self, enable: bool):
        if not hasattr(self, "player_btns"):
            return
        # En Windows el clic derecho es <Button-3>
        for idx, b in enumerate(self.player_btns, start=0):
            if enable:
                # Activar: clic derecho abre menú, doble clic abre editar
                b.bind("<Button-3>", lambda e, n=idx: self._open_score_menu(e, n))
            else:
                # Desactivar: quitar binds
                b.unbind("<Button-3>")

# ---------------------- Clase Panel de Pregunta (embebido) ----------------------

class QuestionPanel(ttk.Frame):
    def _resize_fonts(self, event=None):
        """Ajusta dinámicamente el tamaño de fuente y el wrap según el ancho del panel."""
        try:
            w = max(0, self.winfo_width())
            if w <= 0:
                return
            # Tamaños relativos a la anchura del panel
            base = max(12, int(w / 60))
            q_size = base + 6
            o_size = base
            wrap = int(w * 0.90)

            if hasattr(self, "question_label") and self.question_label.winfo_exists():
                self.question_label.configure(font=("Segoe UI", q_size, "bold"), wraplength=wrap, justify="center")

            self.letra_grande.configure(size=base) #######################

        except Exception:
            pass

    def __init__(self, parent, app: JeopardyApp, cat_idx: int, clue_idx: int, clue: Dict[str, Any]):
        super().__init__(parent, style="White.TFrame")
        self.app = app
        self.cat_idx = cat_idx
        self.clue_idx = clue_idx
        self.value = int(clue.get("value", 100))
        self.question = str(clue.get("question", "(Sin pregunta)"))
        self.choices: List[str] = list(clue.get("choices", []))
        self.answer_idx = int(clue.get("answer", 0)) if self.choices else 0

        container = ttk.Frame(self, padding=12, style="White.TFrame")
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text=f"Valor: {self.value}", font=("Segoe UI", 11, "bold"), background="white").pack(anchor="w")

        # Label de pregunta centrado y escalable
        self.question_label = tk.Label(
            container,
            text=self.question,
            wraplength=900,
            font=("Segoe UI", 14, "bold"),
            bg="white",
            justify="left",
            anchor="w"
        )
        self.question_label.pack(fill=tk.X, pady=(20, 34))

        # Opciones (contenedor para poder ocultarlas/mostrarlas)
        self.choice_var = tk.IntVar(value=-1)
        #self.choice_rbs: List[ttk.Radiobutton] = []
        self.choice_rbs = []
        self.choices_container = ttk.Frame(container, style="White.TFrame")
        #self.choices_container.pack(fill=tk.X, pady=(6, 54))

######################################################

        # Definir una fuente grande
        self.letra_grande = tkfont.Font(family="Segoe UI", size=18, weight="bold")

        # Crear un estilo nuevo
        self.style = ttk.Style(self.choices_container)
        try:
            self.style.theme_use("clam")   #'clam' respeta mejor colores personalizados
        except Exception:
            pass
        self.style.configure("White.TFrame", background="white")
        self.style.configure("Big.TRadiobutton", background="white", foreground="black", font=self.letra_grande)

#######################################################

        for i, opt in enumerate(self.choices):
            prefix = f"{chr(97 + i)}) "  # a), b), c), d)
            #rb = ttk.Radiobutton(self.choices_container, text=prefix + opt, variable=self.choice_var, value=i)
            rb = ttk.Radiobutton(self.choices_container, text=prefix + opt, variable=self.choice_var, value=i, style="Big.TRadiobutton")
            # Fuente inicial (se reescala en _resize_fonts)
            try:
                rb.configure(font=("Segoe UI", 12))
            except Exception:
                pass
            rb.pack(anchor="w", pady=2)
            self.choice_rbs.append(rb)

        # Por defecto, deshabilitar selección hasta que alguien timbre
        self.enable_choices(False)

        status_box = ttk.Frame(container, style="White.TFrame")
        status_box.pack(fill=tk.X, pady=(8, 0))
        self.turn_var = tk.StringVar(value="Esperando timbre…")
        #ttk.Label(status_box, textvariable=self.turn_var, style="Cat.TLabel").pack(side=tk.LEFT)

        # (Sin botones locales aquí; la barra inferior global muestra Responder/Cancelar o Correcto/Incorrecto)

        # Aplicar estado inicial (ocultar/mostrar opciones según checkbox global)
        self.apply_hide_state()

        # Vincular redimensionado y ajustar una vez
        self.bind("<Configure>", self._resize_fonts)
        self._resize_fonts()

        ##################################################################
        # Atajos: Enter = Responder, Esc = Cancelar
        self._bind_keys(True)

    # --- Key bindings ---
    def _bind_keys(self, enable: bool):
        top = self.winfo_toplevel()
        if enable:
            top.bind("<Return>", self._on_enter)
            top.bind("<Escape>", self._on_escape)
        else:
            top.unbind("<Return>")
            top.unbind("<Escape>")

    def _on_enter(self, event=None):
        self.submit()

    def _on_escape(self, event=None):
        self.cancel_turn()
    ###########################################################################

    def set_turn_text(self, text: str):
        self.turn_var.set(text)

    def enable_choices(self, enable: bool):
        state = '!disabled' if enable else 'disabled'
        for rb in self.choice_rbs:
            rb.state([state])

    def reset_selection(self):
        self.choice_var.set(-1)

    def apply_hide_state(self):
        # Muestra u oculta el contenedor de opciones según el checkbox global
        hide = self.app.hide_answers.get() if hasattr(self.app, 'hide_answers') else False
        if hide:
            try:
                self.choices_container.pack_forget()
            except Exception:
                pass
            # Mantener opciones deshabilitadas
            self.enable_choices(False)
        else:
            if self.choices_container.winfo_manager() != 'pack':
                self.choices_container.pack(fill=tk.X)
            # Habilitar si hay turno
            if self.app.current_buzzer is None:
                self.enable_choices(False)
            else:
                self.enable_choices(True)

    def submit(self):
        if self.app.current_buzzer is None:
            self.app.set_status("Primero un jugador debe presionar su timbre.", "info")
            return
        sel = self.choice_var.get()
        if sel < 0:
            self.app.set_status("Selecciona una opción antes de responder.", "info")
            return
        self.app.stop_timer()
        if sel == self.answer_idx:
            self.app.process_answer(self.cat_idx, self.clue_idx, "correct", self.value, self)
        else:
            self.app.process_answer(self.cat_idx, self.clue_idx, "incorrect", self.value, self)
            self.enable_choices(False)
            self.reset_selection()

    def moderator_correct(self):
        if self.app.current_buzzer is None:
            self.app.set_status("Primero un jugador debe presionar su timbre.", "info")
            return
        self.app.stop_timer()
        self.app.process_answer(self.cat_idx, self.clue_idx, "correct", self.value, self)

    def moderator_incorrect(self):
        if self.app.current_buzzer is None:
            self.app.set_status("Primero un jugador debe presionar su timbre.", "info")
            return
        self.app.stop_timer()
        self.app.process_answer(self.cat_idx, self.clue_idx, "incorrect", self.value, self)
        self.enable_choices(False)
        self.reset_selection()

    def cancel_turn(self):
        # Cancelar la pregunta sin afectar puntajes; detener temporizador
        self.app.stop_timer()
        self.app.process_answer(self.cat_idx, self.clue_idx, "cancel", self.value, self)
        #Detener sonido activo (buzzer/intro/timeout/etc.)
        snd = getattr(self.app, "snd", None)
        if snd: snd.stop_all()
 
# ---------------------- main ----------------------
def main():
    data = load_data()
    app = JeopardyApp(data)
    app.main_loop()


if __name__ == "__main__":
    main()
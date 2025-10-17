#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lógica del juego Jeopardy - Migrada desde Tkinter
"""
import json
import csv
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

TIME_LIMIT_SECONDS = 10

# Dataset de respaldo
SAMPLE_DATA = {
    "categories": [
        {
            "name": "Ciencia",
            "clues": [
                {"value": 100, "question": "¿Cuál es el planeta más cercano al Sol?", "choices": ["Venus", "Mercurio", "Marte", "Tierra"], "answer": 1},
                {"value": 200, "question": "¿Qué molécula transporta oxígeno en la sangre?", "choices": ["Insulina", "Hemoglobina", "Glucosa", "Colágeno"], "answer": 1},
                {"value": 300, "question": "¿Qué partícula tiene carga negativa?", "choices": ["Protón", "Neutrón", "Electrón", "Positrón"], "answer": 2},
                {"value": 400, "question": "¿Qué gas es esencial para la respiración humana?", "choices": ["Oxígeno", "Dióxido de carbono", "Nitrógeno", "Hidrógeno"], "answer": 0},
            ],
        },
        {
            "name": "Historia",
            "clues": [
                {"value": 100, "question": "¿En qué año llegó Cristóbal Colón a América?", "choices": ["1492", "1519", "1776", "1453"], "answer": 0},
                {"value": 200, "question": "¿Qué civilización construyó Machu Picchu?", "choices": ["Azteca", "Maya", "Inca", "Olmeca"], "answer": 2},
                {"value": 300, "question": "¿Quién fue conocido como el Libertador de América?", "choices": ["Simón Bolívar", "José de San Martín", "Miguel Hidalgo", "Bernardo O'Higgins"], "answer": 0},
                {"value": 400, "question": "¿En qué año comenzó la Segunda Guerra Mundial?", "choices": ["1935", "1939", "1941", "1945"], "answer": 1},
            ],
        },
        {
            "name": "Tecnología",
            "clues": [
                {"value": 100, "question": "¿Qué significa 'CPU'?", "choices": ["Central Processing Unit", "Computer Personal Unit", "Core Processing Utility", "Central Peripheral Unit"], "answer": 0},
                {"value": 200, "question": "¿Qué protocolo se usa típicamente para la web?", "choices": ["FTP", "SMTP", "HTTP", "SSH"], "answer": 2},
                {"value": 300, "question": "¿Cuál de estos es un lenguaje de programación?", "choices": ["HTML", "CSS", "Python", "JSON"], "answer": 2},
                {"value": 400, "question": "¿Qué protocolo nos permite navegar seguros en la web?", "choices": ["HTTP", "HTTPS", "FTP", "TELNET"], "answer": 1},
            ],
        },
        {
            "name": "Geografía",
            "clues": [
                {"value": 100, "question": "¿Cuál es el río más largo del mundo?", "choices": ["Amazonas", "Nilo", "Yangtsé", "Misisipi"], "answer": 0},
                {"value": 200, "question": "¿En qué continente está Egipto?", "choices": ["Asia", "África", "Europa", "Oceanía"], "answer": 1},
                {"value": 300, "question": "¿Cuál es la capital de Japón?", "choices": ["Pekín", "Seúl", "Tokio", "Osaka"], "answer": 2},
                {"value": 400, "question": "¿Qué país tiene forma de bota?", "choices": ["Grecia", "Italia", "España", "Portugal"], "answer": 1},
            ],
        }
    ]
}


class GameState:
    """Gestiona el estado completo del juego"""
    
    def __init__(self):
        self.data = SAMPLE_DATA
        self.player_scores = [0, 0, 0, 0, 0]
        self.used_questions: Set[Tuple[int, int]] = set()
        self.tile_status: Dict[Tuple[int, int], str] = {}  # 'correct' | 'used'
        self.current_buzzer: Optional[int] = None
        self.tried_players: Set[int] = set()
        self.current_question: Optional[Dict] = None
        self.timer_active = False
        self.hide_answers = False
        
    def reset_game(self):
        """Reinicia el juego completo"""
        self.player_scores = [0, 0, 0, 0, 0]
        self.used_questions.clear()
        self.tile_status.clear()
        self.current_buzzer = None
        self.tried_players.clear()
        self.current_question = None
        self.timer_active = False
        
    def open_question(self, cat_idx: int, clue_idx: int) -> Dict:
        """Abre una pregunta del tablero"""
        if (cat_idx, clue_idx) in self.used_questions:
            return {"error": "Pregunta ya usada"}
            
        cat = self.data["categories"][cat_idx]
        clue = cat["clues"][clue_idx]
        
        self.current_question = {
            "cat_idx": cat_idx,
            "clue_idx": clue_idx,
            "category": cat["name"],
            "value": clue["value"],
            "question": clue["question"],
            "choices": clue["choices"],
            "answer": clue["answer"]
        }
        self.tried_players.clear()
        
        return self.current_question
        
    def buzzer_press(self, player_idx: int) -> Dict:
        """Un jugador presiona su buzzer"""
        if self.current_question is None:
            return {"error": "No hay pregunta activa"}
            
        if self.current_buzzer is not None:
            return {"error": "Ya hay un jugador respondiendo"}
            
        if player_idx in self.tried_players:
            return {"error": "Este jugador ya intentó"}
            
        self.current_buzzer = player_idx
        self.timer_active = True
        
        return {
            "success": True,
            "player": player_idx,
            "message": f"Equipo {player_idx + 1} tiene el turno"
        }
        
    def submit_answer(self, player_idx: int, answer_idx: int) -> Dict:
        """Procesa una respuesta del jugador"""
        if self.current_question is None:
            return {"error": "No hay pregunta activa"}
            
        if self.current_buzzer != player_idx:
            return {"error": "No es tu turno"}
        
        # Asegurar que ambos sean enteros para comparación
        try:
            answer_idx = int(answer_idx)
        except (ValueError, TypeError):
            answer_idx = -1
            
        cat_idx = self.current_question["cat_idx"]
        clue_idx = self.current_question["clue_idx"]
        value = self.current_question["value"]
        correct_answer = int(self.current_question["answer"])
        
        print(f"🔍 Comparando respuestas:")
        print(f"   Recibida: {answer_idx} (tipo: {type(answer_idx).__name__})")
        print(f"   Correcta: {correct_answer} (tipo: {type(correct_answer).__name__})")
        
        is_correct = (answer_idx == correct_answer)
        print(f"   ¿Es correcta? {is_correct}")
        
        if is_correct:
            # Respuesta correcta
            self.player_scores[player_idx] += value
            self.used_questions.add((cat_idx, clue_idx))
            self.tile_status[(cat_idx, clue_idx)] = 'correct'
            self.current_question = None
            self.current_buzzer = None
            self.tried_players.clear()
            self.timer_active = False
            
            return {
                "result": "correct",
                "player": player_idx,
                "new_score": self.player_scores[player_idx],
                "close_question": True
            }
        else:
            # Respuesta incorrecta
            self.player_scores[player_idx] -= value
            self.tried_players.add(player_idx)
            self.current_buzzer = None
            self.timer_active = False
            
            # ¿Quedan jugadores?
            remaining = [i for i in range(5) if i not in self.tried_players]
            
            if remaining:
                # Rebote
                return {
                    "result": "incorrect",
                    "player": player_idx,
                    "new_score": self.player_scores[player_idx],
                    "close_question": False,
                    "rebote": True,
                    "remaining_players": remaining
                }
            else:
                # Sin intentos restantes
                self.used_questions.add((cat_idx, clue_idx))
                self.tile_status[(cat_idx, clue_idx)] = 'used'
                self.current_question = None
                self.tried_players.clear()
                
                return {
                    "result": "incorrect",
                    "player": player_idx,
                    "new_score": self.player_scores[player_idx],
                    "close_question": True,
                    "rebote": False
                }
                
    def moderator_correct(self, player_idx: int) -> Dict:
        """Moderador marca como correcta (modo respuestas ocultas)"""
        if self.current_question is None:
            return {"error": "No hay pregunta activa"}
            
        if self.current_buzzer != player_idx:
            return {"error": "No es el turno de este jugador"}
            
        cat_idx = self.current_question["cat_idx"]
        clue_idx = self.current_question["clue_idx"]
        value = self.current_question["value"]
        
        self.player_scores[player_idx] += value
        self.used_questions.add((cat_idx, clue_idx))
        self.tile_status[(cat_idx, clue_idx)] = 'correct'
        self.current_question = None
        self.current_buzzer = None
        self.tried_players.clear()
        self.timer_active = False
        
        return {
            "result": "correct",
            "player": player_idx,
            "new_score": self.player_scores[player_idx],
            "close_question": True
        }
        
    def moderator_incorrect(self, player_idx: int) -> Dict:
        """Moderador marca como incorrecta (modo respuestas ocultas)"""
        if self.current_question is None:
            return {"error": "No hay pregunta activa"}
            
        if self.current_buzzer != player_idx:
            return {"error": "No es el turno de este jugador"}
            
        cat_idx = self.current_question["cat_idx"]
        clue_idx = self.current_question["clue_idx"]
        value = self.current_question["value"]
        
        self.player_scores[player_idx] -= value
        self.tried_players.add(player_idx)
        self.current_buzzer = None
        self.timer_active = False
        
        remaining = [i for i in range(5) if i not in self.tried_players]
        
        if remaining:
            return {
                "result": "incorrect",
                "player": player_idx,
                "new_score": self.player_scores[player_idx],
                "close_question": False,
                "rebote": True,
                "remaining_players": remaining
            }
        else:
            self.used_questions.add((cat_idx, clue_idx))
            self.tile_status[(cat_idx, clue_idx)] = 'used'
            self.current_question = None
            self.tried_players.clear()
            
            return {
                "result": "incorrect",
                "player": player_idx,
                "new_score": self.player_scores[player_idx],
                "close_question": True,
                "rebote": False
            }
    
    def cancel_question(self) -> Dict:
        """Cancela la pregunta actual sin afectar puntajes"""
        if self.current_question is None:
            return {"error": "No hay pregunta activa"}
            
        self.current_question = None
        self.current_buzzer = None
        self.tried_players.clear()
        self.timer_active = False
        
        return {"success": True, "message": "Pregunta cancelada"}
        
    def timeout(self) -> Dict:
        """Procesa un timeout (tiempo agotado)"""
        if self.current_buzzer is not None:
            return self.submit_answer(self.current_buzzer, -1)  # Respuesta inválida
        return {"error": "No hay jugador activo"}
        
    def adjust_score(self, player_idx: int, delta: int):
        """Ajusta el puntaje de un jugador manualmente"""
        if 0 <= player_idx < 5:
            self.player_scores[player_idx] += delta
            return {"success": True, "new_score": self.player_scores[player_idx]}
        return {"error": "Índice de jugador inválido"}
        
    def set_score(self, player_idx: int, score: int):
        """Establece el puntaje de un jugador directamente"""
        if 0 <= player_idx < 5:
            self.player_scores[player_idx] = score
            return {"success": True, "new_score": self.player_scores[player_idx]}
        return {"error": "Índice de jugador inválido"}
        
    def get_board_state(self) -> Dict:
        """Obtiene el estado actual del tablero"""
        return {
            "categories": self.data["categories"],
            "used": list(self.used_questions),
            "tile_status": {f"{k[0]},{k[1]}": v for k, v in self.tile_status.items()},
            "scores": self.player_scores
        }
        
    def get_game_state(self) -> Dict:
        """Obtiene el estado completo del juego"""
        return {
            "scores": self.player_scores,
            "current_buzzer": self.current_buzzer,
            "tried_players": list(self.tried_players),
            "timer_active": self.timer_active,
            "hide_answers": self.hide_answers,
            "has_question": self.current_question is not None
        }


# Funciones de carga de datos (reutilizadas del código original)

def load_data(path: str = "data/questions.json") -> Dict[str, Any]:
    """Carga datos desde JSON"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "categories" not in data:
            return SAMPLE_DATA
        return data
    except Exception:
        return SAMPLE_DATA


def _read_used_ids(used_csv_path: str) -> Set[int]:
    """Lee usadas.csv y devuelve conjunto de IDs ya utilizados"""
    used = set()
    p = Path(used_csv_path)
    if not p.exists():
        return used
    try:
        with p.open("r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                raw = (row.get("idpregunta") or row.get("id") or "").strip()
                if raw:
                    try:
                        used.add(int(raw))
                    except ValueError:
                        pass
    except Exception:
        pass
    return used


def _append_used_rows(used_csv_path: str, rows: List[dict]):
    """Anexa filas a usadas.csv"""
    p = Path(used_csv_path)
    exists = p.exists()
    try:
        with p.open("a", encoding="utf-8", newline="") as f:
            fieldnames = ["idpregunta", "category", "value", "question", "choice_a", "choice_b", "choice_c", "choice_d", "answer"]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            if not exists:
                w.writeheader()
            for row in rows:
                w.writerow({
                    "idpregunta": row.get("idpregunta"),
                    "category": row.get("category", ""),
                    "value": row.get("value", 0),
                    "question": row.get("question", ""),
                    "choice_a": (row.get("choices", ["", "", "", ""])[0] if "choices" in row else row.get("choice_a", "")),
                    "choice_b": (row.get("choices", ["", "", "", ""])[1] if "choices" in row else row.get("choice_b", "")),
                    "choice_c": (row.get("choices", ["", "", "", ""])[2] if "choices" in row else row.get("choice_c", "")),
                    "choice_d": (row.get("choices", ["", "", "", ""])[3] if "choices" in row else row.get("choice_d", "")),
                    "answer": row.get("answer", 0),
                })
    except Exception as e:
        print(f"Error guardando en usadas.csv: {e}")


def load_from_csv_sampled(
    path: str,
    used_csv_path: str = "data/usadas.csv",
    values_per_category=(100, 200, 300, 400, 500),
    rng_seed: Optional[int] = None
) -> dict:
    """Carga CSV con muestreo aleatorio excluyendo usadas"""
    if rng_seed is not None:
        random.seed(rng_seed)
        
    used_ids = _read_used_ids(used_csv_path)
    def _load_bucket_with_encoding(encoding: str) -> Dict[Tuple[str, int], List[dict]]:
        bucket_local: Dict[Tuple[str, int], List[dict]] = {}
        with open(path, "r", encoding=encoding, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    qid = int(str(row.get("idpregunta", "")).strip())
                except ValueError:
                    continue

                cat = (row.get("category") or "General").strip()
                try:
                    val = int(str(row.get("value", "0")).strip())
                except ValueError:
                    continue

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
                    try:
                        answer = int(ans_raw)
                    except:
                        answer = 0

                bucket_local.setdefault((cat, val), []).append({
                    "idpregunta": qid,
                    "category": cat,
                    "value": val,
                    "question": question,
                    "choices": choices,
                    "answer": answer,
                })
        return bucket_local

    bucket: Dict[Tuple[str, int], List[dict]] = {}
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error: Optional[Exception] = None

    for enc in encodings_to_try:
        try:
            bucket = _load_bucket_with_encoding(enc)
            break
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except FileNotFoundError as e:
            raise e
        except Exception as e:
            print(f"Error leyendo CSV: {e}")
            return SAMPLE_DATA
    else:
        print(f"Error leyendo CSV: {last_error}")
        return SAMPLE_DATA
        
    categories = {}
    cats_in_csv = sorted({cat for (cat, _) in bucket.keys()})
    used_rows_to_append = []
    
    for cat in cats_in_csv:
        clues = []
        for val in values_per_category:
            pool = bucket.get((cat, val), [])
            fresh = [r for r in pool if r["idpregunta"] not in used_ids]
            
            if fresh:
                pick = random.choice(fresh)
            elif pool:
                raise ValueError("No hay suficientes preguntas para otra ronda")
            else:
                pick = {
                    "idpregunta": None,
                    "category": cat,
                    "value": val,
                    "question": f"(Sin pregunta disponible para {cat} {val})",
                    "choices": ["", "", "", ""],
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
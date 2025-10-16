#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Flask para Jeopardy Web
WebSockets para comunicación en tiempo real
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import game_logic
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jeopardy_secret_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Instancia global del juego
game = game_logic.GameState()

# =====================
# RUTAS HTTP
# =====================

@app.route('/')
def index():
    """Página principal del juego"""
    return render_template('index.html')

@app.route('/api/board')
def get_board():
    """Obtiene el estado del tablero"""
    return jsonify(game.get_board_state())

@app.route('/api/game-state')
def get_game_state():
    """Obtiene el estado completo del juego"""
    return jsonify(game.get_game_state())

@app.route('/api/load-data', methods=['POST'])
def load_data():
    """Carga datos desde JSON o CSV"""
    data = request.get_json()
    file_type = data.get('type', 'json')
    file_path = data.get('path', '')
    
    try:
        if file_type == 'csv':
            game.data = game_logic.load_from_csv_sampled(
                file_path,
                used_csv_path="data/usadas.csv"
            )
        else:
            game.data = game_logic.load_data(file_path)
            
        game.reset_game()
        
        # Notificar a todos los clientes
        socketio.emit('game_reset', game.get_board_state())
        
        return jsonify({"success": True, "message": "Datos cargados correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/reset', methods=['POST'])
def reset_game():
    """Reinicia el juego"""
    game.reset_game()
    socketio.emit('game_reset', game.get_board_state())
    return jsonify({"success": True})

# =====================
# WEBSOCKET EVENTS
# =====================

@socketio.on('connect')
def handle_connect():
    """Cliente se conecta"""
    print("Cliente conectado")
    emit('connected', {
        'board': game.get_board_state(),
        'game_state': game.get_game_state()
    })

@socketio.on('open_question')
def handle_open_question(data):
    """Abre una pregunta del tablero"""
    cat_idx = data.get('cat_idx')
    clue_idx = data.get('clue_idx')
    
    result = game.open_question(cat_idx, clue_idx)
    
    if 'error' in result:
        emit('error', result, broadcast=False)
    else:
        # Enviar pregunta (con o sin respuestas según modo)
        question_data = result.copy()
        if game.hide_answers:
            question_data.pop('answer', None)
            question_data.pop('choices', None)
        
        emit('question_opened', question_data, broadcast=True)

@socketio.on('buzzer_press')
def handle_buzzer(data):
    """Un jugador presiona su buzzer"""
    player_idx = data.get('player')
    
    result = game.buzzer_press(player_idx)
    
    if 'error' in result:
        emit('error', result, broadcast=False)
    else:
        emit('buzzer_activated', result, broadcast=True)
        # Iniciar temporizador del lado del cliente
        emit('start_timer', {'seconds': game_logic.TIME_LIMIT_SECONDS}, broadcast=True)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Jugador envía su respuesta"""
    player_idx = data.get('player')
    answer_idx = data.get('answer')
    
    result = game.submit_answer(player_idx, answer_idx)
    
    if 'error' in result:
        emit('error', result, broadcast=False)
    else:
        emit('answer_result', result, broadcast=True)
        emit('stop_timer', {}, broadcast=True)
        
        # Actualizar scores
        emit('scores_update', {'scores': game.player_scores}, broadcast=True)
        
        if result.get('close_question'):
            emit('close_question', {}, broadcast=True)

@socketio.on('moderator_correct')
def handle_moderator_correct(data):
    """Moderador marca como correcta (modo ocultar respuestas)"""
    player_idx = data.get('player')
    
    result = game.moderator_correct(player_idx)
    
    if 'error' in result:
        emit('error', result, broadcast=False)
    else:
        emit('answer_result', result, broadcast=True)
        emit('stop_timer', {}, broadcast=True)
        emit('scores_update', {'scores': game.player_scores}, broadcast=True)
        emit('close_question', {}, broadcast=True)

@socketio.on('moderator_incorrect')
def handle_moderator_incorrect(data):
    """Moderador marca como incorrecta (modo ocultar respuestas)"""
    player_idx = data.get('player')
    
    result = game.moderator_incorrect(player_idx)
    
    if 'error' in result:
        emit('error', result, broadcast=False)
    else:
        emit('answer_result', result, broadcast=True)
        emit('stop_timer', {}, broadcast=True)
        emit('scores_update', {'scores': game.player_scores}, broadcast=True)
        
        if result.get('close_question'):
            emit('close_question', {}, broadcast=True)

@socketio.on('cancel_question')
def handle_cancel():
    """Cancela la pregunta actual"""
    result = game.cancel_question()
    
    if 'error' in result:
        emit('error', result, broadcast=False)
    else:
        emit('stop_timer', {}, broadcast=True)
        emit('close_question', {}, broadcast=True)

@socketio.on('timeout')
def handle_timeout():
    """Tiempo agotado"""
    result = game.timeout()
    
    emit('answer_result', result, broadcast=True)
    emit('scores_update', {'scores': game.player_scores}, broadcast=True)
    
    if result.get('close_question'):
        emit('close_question', {}, broadcast=True)

@socketio.on('toggle_hide_answers')
def handle_toggle_hide(data):
    """Cambia el modo de ocultar/mostrar respuestas"""
    game.hide_answers = data.get('hide', False)
    emit('hide_answers_toggled', {'hide': game.hide_answers}, broadcast=True)

@socketio.on('adjust_score')
def handle_adjust_score(data):
    """Ajusta el puntaje de un jugador"""
    player_idx = data.get('player')
    delta = data.get('delta', 0)
    
    result = game.adjust_score(player_idx, delta)
    
    if 'error' in result:
        emit('error', result, broadcast=False)
    else:
        emit('scores_update', {'scores': game.player_scores}, broadcast=True)

@socketio.on('set_score')
def handle_set_score(data):
    """Establece el puntaje de un jugador directamente"""
    player_idx = data.get('player')
    score = data.get('score', 0)
    
    result = game.set_score(player_idx, score)
    
    if 'error' in result:
        emit('error', result, broadcast=False)
    else:
        emit('scores_update', {'scores': game.player_scores}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente se desconecta"""
    print("Cliente desconectado")

# =====================
# MANEJO DE ARCHIVOS ESTÁTICOS
# =====================

@app.route('/sounds/<path:filename>')
def serve_sound(filename):
    """Sirve archivos de sonido"""
    return send_from_directory('static/sounds', filename)

# =====================
# INICIAR SERVIDOR
# =====================

if __name__ == '__main__':
    # Crear directorios si no existen
    os.makedirs('data', exist_ok=True)
    os.makedirs('static/sounds', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    print("\n" + "="*50)
    print("🎮 JEOPARDY WEB - Servidor Iniciado")
    print("="*50)
    print("📍 URL: http://localhost:5000")
    print("📍 Red local: http://[tu-ip]:5000")
    print("\n🎯 Controles:")
    print("   - Teclado 1-5: Buzzers de equipos")
    print("   - Teclado A-D: Seleccionar respuestas")
    print("   - Enter: Confirmar respuesta")
    print("   - Escape: Cancelar")
    print("\n⚡ WebSockets activos para tiempo real")
    print("="*50 + "\n")
    
    # Iniciar servidor con eventlet para mejor rendimiento
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
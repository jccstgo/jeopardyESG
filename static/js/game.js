// ===========================
// JEOPARDY WEB - CLIENTE
// ===========================

// Estado global
const gameState = {
    currentQuestion: null,
    currentBuzzer: null,
    hideAnswers: false,
    selectedAnswer: -1,
    triedPlayers: new Set(),
    timerInterval: null,
    contextMenuPlayer: null
};

// Conexión WebSocket
const socket = io();

// Elementos del DOM
const elements = {
    board: document.getElementById('board'),
    questionPanel: document.getElementById('question-panel'),
    boardContainer: document.getElementById('board-container'),
    statusBar: document.getElementById('status-bar'),
    timer: document.getElementById('timer'),
    boardControls: document.getElementById('board-controls'),
    panelControls: document.getElementById('panel-controls'),
    moderatorControls: document.getElementById('moderator-controls'),
    hideAnswersCheckbox: document.getElementById('hide-answers')
};

// Algunos templates antiguos incluían múltiples instancias del menú contextual de
// puntajes. Si detectamos copias extra, las eliminamos para evitar que se
// muestre un segundo menú.
const scoreMenus = document.querySelectorAll('#score-menu');
scoreMenus.forEach((menuEl, idx) => {
    if (idx > 0) {
        menuEl.remove();
    }
});

// Sonidos
const sounds = {
    buzz: new Audio('/sounds/boton_presionado2.wav'),
    correct: new Audio('/sounds/aplausos.wav'),
    incorrect: new Audio('/sounds/incorrecto.wav'),
    countdown: new Audio('/sounds/contestando.wav')
};

// ===========================
// INICIALIZACIÓN
// ===========================

socket.on('connect', () => {
    console.log('✅ Conectado al servidor');
    setStatus('Conectado. Cargando juego...', 'info');
});

socket.on('connected', (data) => {
    console.log('📊 Estado inicial recibido');
    renderBoard(data.board);
    updateScores(data.board.scores);
    setStatus('Selecciona una casilla para abrir una pregunta', 'info');
});

// ===========================
// EVENTOS DEL SERVIDOR
// ===========================

socket.on('question_opened', (data) => {
    console.log('❓ Pregunta abierta:', data);
    gameState.currentQuestion = data;
    gameState.selectedAnswer = -1;
    gameState.triedPlayers = new Set();
    
    // Ocultar panel de ajuste si está visible
    document.getElementById('quick-adjust-panel').style.display = 'none';
    
    showQuestionPanel(data);
    enableBuzzers(true);
    setStatus('Pregunta abierta. ¡Toca tu timbre para responder!', 'info');
});

socket.on('buzzer_activated', (data) => {
    console.log('🔔 Buzzer presionado:', data);
    gameState.currentBuzzer = data.player;
    
    playSound('buzz');
    updateBuzzerButtons();
    setStatus(`Equipo ${data.player + 1} tiene el turno. ¡Responde!`, 'info');
    
    // Habilitar opciones si están visibles
    if (!gameState.hideAnswers) {
        console.log('✅ Habilitando opciones para el jugador');
        enableChoices(true);
    } else {
        console.log('🔒 Opciones ocultas (modo moderador)');
    }
});

socket.on('start_timer', (data) => {
    console.log('⏱️ Temporizador iniciado');
    startTimer(data.seconds);
});

socket.on('stop_timer', () => {
    console.log('⏹️ Temporizador detenido');
    stopTimer();
});

socket.on('answer_result', (data) => {
    console.log('📝 Resultado:', data);
    
    if (data.result === 'correct') {
        playSound('correct');
        flashStatus('correct', 'CORRECTO', '¡Correcto! Elige otra casilla.');
    } else {
        playSound('incorrect');
        
        if (data.rebote) {
            flashStatus('incorrect', 'INCORRECTO', 'Rebote: otro equipo puede contestar.');
            gameState.triedPlayers.add(data.player);
            gameState.currentBuzzer = null;
            updateBuzzerButtons();
            enableChoices(false);
            gameState.selectedAnswer = -1;
        } else {
            flashStatus('incorrect', 'INCORRECTO', 'Sin intentos restantes. Elige otra casilla.');
        }
    }
});

socket.on('scores_update', (data) => {
    console.log('💯 Puntajes actualizados');
    updateScores(data.scores);
});

socket.on('close_question', () => {
    console.log('❌ Pregunta cerrada');
    closeQuestionPanel();
    enableBuzzers(false);
    gameState.currentQuestion = null;
    gameState.currentBuzzer = null;
    gameState.triedPlayers.clear();
    gameState.selectedAnswer = -1;
    
    // Asegurar que los controles vuelvan al modo tablero
    updateControlsMode();
    
    // Recargar tablero
    fetch('/api/board')
        .then(r => r.json())
        .then(data => renderBoard(data));
});

socket.on('game_reset', (data) => {
    console.log('🔄 Juego reiniciado');
    renderBoard(data);
    updateScores(data.scores);
    closeQuestionPanel();
    gameState.currentQuestion = null;
    gameState.currentBuzzer = null;
    gameState.selectedAnswer = -1;
    gameState.triedPlayers.clear();
    updateControlsMode();
    setStatus('Juego reiniciado. Selecciona una casilla.', 'info');
});

socket.on('hide_answers_toggled', (data) => {
    gameState.hideAnswers = data.hide;
    updateControlsMode();
});

socket.on('error', (data) => {
    console.error('❌ Error:', data);
    setStatus(data.error || 'Error desconocido', 'incorrect');
});

// ===========================
// RENDERIZADO DEL TABLERO
// ===========================

function renderBoard(data) {
    const categories = data.categories || [];
    const used = new Set(data.used.map(([c, r]) => `${c}-${r}`));
    const tileStatus = data.tile_status || {};
    
    if (categories.length === 0) {
        elements.board.innerHTML = '<div style="text-align:center">No hay categorías</div>';
        return;
    }
    
    const maxClues = Math.max(...categories.map(c => c.clues?.length || 0));
    
    // Configurar grid
    elements.board.style.gridTemplateColumns = `repeat(${categories.length}, 1fr)`;
    elements.board.style.gridTemplateRows = `auto repeat(${maxClues}, 1fr)`;
    
    elements.board.innerHTML = '';
    
    // Encabezados
    categories.forEach(cat => {
        const header = document.createElement('div');
        header.className = 'board-cell header';
        header.textContent = cat.name || 'Categoría';
        elements.board.appendChild(header);
    });
    
    // Celdas
    for (let row = 0; row < maxClues; row++) {
        categories.forEach((cat, catIdx) => {
            const clue = cat.clues?.[row];
            const cell = document.createElement('div');
            cell.className = 'board-cell clue';
            
            // Animación escalonada
            cell.style.animation = `slideInScale 0.5s ease backwards`;
            cell.style.animationDelay = `${(catIdx * 0.1) + (row * 0.05)}s`;
            
            if (clue) {
                const key = `${catIdx},${row}`;
                const status = tileStatus[key];
                const value = clue.value || ((row + 1) * 100);
                
                cell.textContent = value;
                cell.dataset.catIdx = catIdx;
                cell.dataset.clueIdx = row;
                
                if (status === 'correct') {
                    cell.classList.add('correct');
                } else if (status === 'used' || used.has(`${catIdx}-${row}`)) {
                    cell.classList.add('used');
                } else {
                    cell.onclick = () => openQuestion(catIdx, row);
                }
            } else {
                cell.textContent = '—';
                cell.classList.add('used');
            }
            
            elements.board.appendChild(cell);
        });
    }
    
    // Agregar keyframe para animación de entrada
    if (!document.getElementById('board-animation-keyframe')) {
        const style = document.createElement('style');
        style.id = 'board-animation-keyframe';
        style.textContent = `
            @keyframes slideInScale {
                from {
                    opacity: 0;
                    transform: scale(0.5) translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Asegurar que estamos en modo tablero
    gameState.currentQuestion = null;
    updateControlsMode();
}

// ===========================
// PANEL DE PREGUNTA
// ===========================

function showQuestionPanel(question) {
    elements.boardContainer.style.display = 'none';
    elements.questionPanel.style.display = 'block';
    
    document.getElementById('question-category').textContent = question.category;
    document.getElementById('question-value').textContent = `Valor: ${question.value}`;
    document.getElementById('question-text').textContent = question.question;
    document.getElementById('question-status').textContent = 'Esperando timbre...';
    
    // Renderizar opciones
    const choicesContainer = document.getElementById('choices-container');
    choicesContainer.innerHTML = '';
    
    if (question.choices && !gameState.hideAnswers) {
        question.choices.forEach((choice, idx) => {
            const option = document.createElement('div');
            option.className = 'choice-option disabled';
            option.dataset.index = idx;
            
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'answer';
            radio.value = idx;
            radio.disabled = true;
            radio.id = `choice-${idx}`;
            
            // Event listener para el radio button
            radio.addEventListener('change', () => {
                if (!radio.disabled) {
                    selectChoice(idx);
                }
            });
            
            const label = document.createElement('label');
            label.htmlFor = `choice-${idx}`;
            label.textContent = `${String.fromCharCode(97 + idx)}) ${choice}`;
            label.style.cursor = 'pointer';
            label.style.flex = '1';
            
            option.appendChild(radio);
            option.appendChild(label);
            
            // Event listener para el div completo
            option.addEventListener('click', (e) => {
                if (!option.classList.contains('disabled')) {
                    selectChoice(idx);
                }
            });
            
            choicesContainer.appendChild(option);
        });
    } else if (gameState.hideAnswers) {
        choicesContainer.innerHTML = '<p style="text-align:center;color:#666;">Modo moderador: respuestas ocultas</p>';
    }
    
    updateControlsMode();
}

function closeQuestionPanel() {
    console.log('🔙 Cerrando panel de pregunta, volviendo al tablero');
    
    elements.questionPanel.style.display = 'none';
    elements.boardContainer.style.display = 'block';
    
    // Limpiar estado
    gameState.currentQuestion = null;
    gameState.selectedAnswer = -1;
    
    // Restaurar controles del tablero
    updateControlsMode();
}

function selectChoice(index) {
    if (gameState.currentBuzzer === null) {
        console.warn('⚠️ No hay jugador con turno activo');
        return;
    }
    
    console.log(`🎯 Seleccionando opción: ${index} (${String.fromCharCode(97 + index)})`);
    gameState.selectedAnswer = parseInt(index);
    
    // Actualizar UI
    document.querySelectorAll('.choice-option').forEach((option, idx) => {
        const isSelected = (idx === parseInt(index));
        option.classList.toggle('selected', isSelected);
        
        const radio = option.querySelector('input');
        if (radio) {
            radio.checked = isSelected;
        }
        
        if (isSelected) {
            console.log(`✓ Opción ${String.fromCharCode(97 + idx)} seleccionada`);
        }
    });
    
    // Mostrar en status
    setStatus(`Opción ${String.fromCharCode(97 + index)} seleccionada. Presiona Enter para confirmar.`, 'info');
}

function enableChoices(enable) {
    console.log(`🎛️ ${enable ? 'Habilitando' : 'Deshabilitando'} opciones de respuesta`);
    
    document.querySelectorAll('.choice-option').forEach(option => {
        const radio = option.querySelector('input');
        
        if (enable) {
            option.classList.remove('disabled');
            option.style.pointerEvents = 'auto';
            option.style.cursor = 'pointer';
            if (radio) {
                radio.disabled = false;
            }
        } else {
            option.classList.add('disabled');
            option.style.pointerEvents = 'none';
            option.style.cursor = 'not-allowed';
            if (radio) {
                radio.disabled = true;
            }
        }
    });
}

// ===========================
// ACCIONES DEL JUEGO
// ===========================

function openQuestion(catIdx, clueIdx) {
    console.log('🎯 Abriendo pregunta:', catIdx, clueIdx);
    socket.emit('open_question', { cat_idx: catIdx, clue_idx: clueIdx });
}

function pressBuzzer(playerIdx) {
    if (gameState.triedPlayers.has(playerIdx)) {
        console.log('⚠️ Jugador ya intentó');
        return;
    }
    
    console.log('🔔 Presionando buzzer:', playerIdx);
    socket.emit('buzzer_press', { player: playerIdx });
}

function submitAnswer() {
    console.log('🚀 Intentando enviar respuesta...');
    console.log('   - Buzzer actual:', gameState.currentBuzzer);
    console.log('   - Respuesta seleccionada:', gameState.selectedAnswer);
    
    if (gameState.currentBuzzer === null) {
        setStatus('Primero un jugador debe presionar su timbre', 'incorrect');
        console.error('❌ No hay jugador con turno activo');
        return;
    }
    
    if (gameState.selectedAnswer < 0) {
        setStatus('Selecciona una opción antes de responder', 'incorrect');
        console.error('❌ No hay respuesta seleccionada (valor:', gameState.selectedAnswer, ')');
        return;
    }
    
    console.log('📤 Enviando respuesta:');
    console.log('  - Jugador:', gameState.currentBuzzer);
    console.log('  - Respuesta seleccionada:', gameState.selectedAnswer);
    console.log('  - Pregunta actual:', gameState.currentQuestion);
    console.log('  - Respuesta correcta esperada:', gameState.currentQuestion?.answer);
    
    socket.emit('submit_answer', {
        player: gameState.currentBuzzer,
        answer: gameState.selectedAnswer
    });
}

function moderatorCorrect() {
    if (gameState.currentBuzzer === null) {
        setStatus('Primero un jugador debe presionar su timbre', 'incorrect');
        return;
    }
    
    console.log('✅ Moderador: Correcto');
    socket.emit('moderator_correct', { player: gameState.currentBuzzer });
}

function moderatorIncorrect() {
    if (gameState.currentBuzzer === null) {
        setStatus('Primero un jugador debe presionar su timbre', 'incorrect');
        return;
    }
    
    console.log('❌ Moderador: Incorrecto');
    socket.emit('moderator_incorrect', { player: gameState.currentBuzzer });
}

function cancelQuestion() {
    console.log('🚫 Cancelando pregunta');
    socket.emit('cancel_question');
    stopAllSounds();
}

function toggleHideAnswers() {
    gameState.hideAnswers = elements.hideAnswersCheckbox.checked;
    socket.emit('toggle_hide_answers', { hide: gameState.hideAnswers });
    
    // Si hay una pregunta abierta, actualizar vista
    if (gameState.currentQuestion) {
        showQuestionPanel(gameState.currentQuestion);
    }
}

function resetGame() {
    if (confirm('¿Deseas reiniciar el juego? Se perderán todos los puntajes.')) {
        fetch('/api/reset', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                console.log('🔄 Juego reiniciado');
            })
            .catch(err => console.error('Error al reiniciar:', err));
    }
}

function loadData() {
    // Por simplicidad, cargar datos de ejemplo
    // En producción, podrías usar un file input
    const path = prompt('Ruta del archivo (JSON o CSV):', 'data/questions.json');
    if (!path) return;
    
    const type = path.toLowerCase().endsWith('.csv') ? 'csv' : 'json';
    
    fetch('/api/load-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, path })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                setStatus(data.message, 'correct');
            } else {
                setStatus(data.error || 'Error al cargar', 'incorrect');
            }
        })
        .catch(err => {
            console.error('Error:', err);
            setStatus('Error al cargar archivo', 'incorrect');
        });
}

function confirmExit() {
    if (confirm('¿Deseas salir del juego?')) {
        window.close();
        // Si no puede cerrar la ventana, mostrar mensaje
        setTimeout(() => {
            setStatus('Cierra esta pestaña para salir', 'info');
        }, 100);
    }
}

// ===========================
// TEMPORIZADOR
// ===========================

function startTimer(seconds) {
    stopTimer(); // Detener temporizador previo
    
    let remaining = seconds;
    elements.timer.textContent = remaining;
    elements.timer.style.color = '#FF3333';
    
    gameState.timerInterval = setInterval(() => {
        remaining--;
        elements.timer.textContent = remaining;
        
        // Cambiar color según tiempo restante
        if (remaining <= 3) {
            elements.timer.style.color = '#FF0000';
            elements.timer.style.fontSize = '42px';
            elements.timer.style.animation = 'timerUrgent 0.5s infinite';
        } else if (remaining <= 6) {
            elements.timer.style.color = '#FF6B00';
            elements.timer.style.fontSize = '38px';
        }
        
        // Sonido a los 6 segundos
        if (remaining === 6) {
            playSound('countdown');
        }
        
        if (remaining <= 0) {
            stopTimer();
            socket.emit('timeout');
        }
    }, 1000);
    
    // Agregar animación de urgencia
    if (!document.getElementById('timer-urgent-keyframe')) {
        const style = document.createElement('style');
        style.id = 'timer-urgent-keyframe';
        style.textContent = `
            @keyframes timerUrgent {
                0%, 100% { 
                    transform: scale(1); 
                    box-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
                }
                50% { 
                    transform: scale(1.1); 
                    box-shadow: 0 0 40px rgba(255, 0, 0, 0.9);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

function stopTimer() {
    if (gameState.timerInterval) {
        clearInterval(gameState.timerInterval);
        gameState.timerInterval = null;
    }
    elements.timer.textContent = '—';
    elements.timer.style.color = '#FF3333';
    elements.timer.style.fontSize = '36px';
    elements.timer.style.animation = '';
    stopSound('countdown');
}

// ===========================
// BUZZER BUTTONS
// ===========================

function enableBuzzers(enable) {
    document.querySelectorAll('.buzzer-btn').forEach((btn, idx) => {
        if (enable && !gameState.triedPlayers.has(idx)) {
            btn.disabled = false;
        } else {
            btn.disabled = true;
        }
    });
    
    if (!enable) {
        gameState.currentBuzzer = null;
    }
    
    updateBuzzerButtons();
}

function updateBuzzerButtons() {
    document.querySelectorAll('.buzzer-btn').forEach((btn, idx) => {
        if (gameState.currentBuzzer === idx) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// ===========================
// PUNTAJES
// ===========================

function updateScores(scores) {
    document.querySelectorAll('.player').forEach((player, idx) => {
        const scoreEl = player.querySelector('.score');
        if (scoreEl) {
            scoreEl.textContent = scores[idx] || 0;
        }
    });
    
    // Actualizar panel de ajuste rápido si está visible
    if (document.getElementById('quick-adjust-panel').style.display !== 'none') {
        updateQuickAdjustScores();
    }
}

// Menú contextual para ajustar puntajes
// Nota: los botones de timbre suelen estar deshabilitados, por lo que no
// reciben eventos de contexto. Asociamos el menú al contenedor completo del
// jugador para garantizar que el clic derecho funcione siempre.
document.querySelectorAll('.player').forEach((playerEl, idx) => {
    playerEl.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        e.stopPropagation();
        showScoreMenu(e, idx);
    });
});

// Prevenir menú contextual del navegador en el área de juego
document.getElementById('app').addEventListener('contextmenu', (e) => {
    // Solo prevenir si es sobre un botón de buzzer
    if (e.target.classList.contains('buzzer-btn') || e.target.closest('.buzzer-btn')) {
        e.preventDefault();
    }
});

function showScoreMenu(event, playerIdx) {
    const menu = document.getElementById('score-menu');
    gameState.contextMenuPlayer = playerIdx;

    // Si el menú está dentro de un contenedor con z-index menor (como el header),
    // lo movemos al <body> la primera vez para que pueda quedar por encima del
    // overlay semitransparente. De lo contrario el overlay bloquea la interacción.
    if (menu.parentElement !== document.body) {
        // Guardar el contenedor original para referencia futura si es necesario.
        if (!menu.dataset.originalParent) {
            menu.dataset.originalParent = menu.parentElement.id || '';
        }
        document.body.appendChild(menu);
    }

    // Crear overlay si no existe
    let overlay = document.getElementById('menu-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'menu-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 99998;
            animation: fadeIn 0.15s ease;
        `;
        document.body.appendChild(overlay);
        
        // Cerrar menú al hacer clic en el overlay
        overlay.addEventListener('click', () => {
            closeScoreMenu();
        });
    }
    
    menu.style.display = 'block';
    
    // Posicionar el menú
    let left = event.pageX;
    let top = event.pageY;
    
    // Forzar renderizado para obtener dimensiones correctas
    menu.style.visibility = 'hidden';
    menu.style.display = 'block';
    const menuRect = menu.getBoundingClientRect();
    menu.style.visibility = 'visible';
    
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Si se sale por la derecha
    if (left + menuRect.width > viewportWidth - 10) {
        left = viewportWidth - menuRect.width - 10;
    }
    
    // Si se sale por abajo
    if (top + menuRect.height > viewportHeight - 10) {
        top = viewportHeight - menuRect.height - 10;
    }
    
    // Asegurar que no esté fuera por arriba o izquierda
    if (left < 10) left = 10;
    if (top < 10) top = 10;
    
    menu.style.left = left + 'px';
    menu.style.top = top + 'px';
    
    console.log('📋 Menú contextual abierto para Equipo', playerIdx + 1);
}

// Cerrar menú con tecla Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const menu = document.getElementById('score-menu');
        if (menu.style.display === 'block') {
            closeScoreMenu();
        }
    }
});

// Cerrar menú al hacer clic fuera de él
document.addEventListener('click', (event) => {
    const menu = document.getElementById('score-menu');

    // Salir si el menú no está visible
    if (!menu || menu.style.display !== 'block') {
        return;
    }

    // Ignorar clics dentro del menú contextual
    if (menu.contains(event.target)) {
        return;
    }

    closeScoreMenu();
});

function closeScoreMenu() {
    const menu = document.getElementById('score-menu');
    const overlay = document.getElementById('menu-overlay');

    menu.style.display = 'none';
    if (overlay) overlay.remove();
    gameState.contextMenuPlayer = null;

    console.log('📋 Menú contextual cerrado');
}

function adjustScore(player, delta) {
    const playerIdx = gameState.contextMenuPlayer;
    if (playerIdx === null || playerIdx < 0 || playerIdx >= 5) return;
    
    console.log(`💰 Ajustando puntaje: Jugador ${playerIdx + 1}, Delta: ${delta}`);
    socket.emit('adjust_score', { player: playerIdx, delta });
    
    // Feedback visual
    showScoreAdjustFeedback(playerIdx, delta);
    
    // Cerrar menú
    closeScoreMenu();
}

function adjustScoreByQuestionValue(player, multiplier) {
    const playerIdx = gameState.contextMenuPlayer;
    if (playerIdx === null || playerIdx < 0 || playerIdx >= 5) return;
    
    // Obtener el valor de la última pregunta o usar 100 por defecto
    let value = 100;
    if (gameState.currentQuestion && gameState.currentQuestion.value) {
        value = gameState.currentQuestion.value;
    }
    
    const delta = value * multiplier;
    console.log(`💰 Ajustando por valor de pregunta: ${value} x ${multiplier} = ${delta}`);
    
    socket.emit('adjust_score', { player: playerIdx, delta });
    showScoreAdjustFeedback(playerIdx, delta);
    
    // Cerrar menú
    closeScoreMenu();
}

function editScore() {
    const playerIdx = gameState.contextMenuPlayer;
    if (playerIdx === null || playerIdx < 0 || playerIdx >= 5) return;
    
    // Cerrar menú primero
    closeScoreMenu();
    
    const currentScore = parseInt(document.querySelectorAll('.score')[playerIdx].textContent) || 0;
    const newScore = prompt(`Nuevo puntaje para Equipo ${playerIdx + 1}:`, currentScore);
    
    if (newScore !== null && !isNaN(newScore)) {
        socket.emit('set_score', { player: playerIdx, score: parseInt(newScore) });
        showScoreAdjustFeedback(playerIdx, parseInt(newScore) - currentScore);
    }
}

function resetPlayerScore() {
    const playerIdx = gameState.contextMenuPlayer;
    if (playerIdx === null || playerIdx < 0 || playerIdx >= 5) return;
    
    // Cerrar menú primero
    closeScoreMenu();
    
    if (confirm(`¿Reiniciar puntaje del Equipo ${playerIdx + 1} a 0?`)) {
        const currentScore = parseInt(document.querySelectorAll('.score')[playerIdx].textContent) || 0;
        socket.emit('set_score', { player: playerIdx, score: 0 });
        showScoreAdjustFeedback(playerIdx, -currentScore);
    }
}

function quickAdjust(playerIdx, delta) {
    if (playerIdx < 0 || playerIdx >= 5) return;
    
    console.log(`⚡ Ajuste rápido: Jugador ${playerIdx + 1}, Delta: ${delta}`);
    socket.emit('adjust_score', { player: playerIdx, delta });
    showScoreAdjustFeedback(playerIdx, delta);
}

function showScoreAdjustFeedback(playerIdx, delta) {
    const scoreEl = document.querySelectorAll('.score')[playerIdx];
    if (!scoreEl) return;
    
    // Crear elemento de feedback flotante
    const feedback = document.createElement('div');
    feedback.style.position = 'fixed';
    feedback.style.zIndex = '10000';
    feedback.style.fontSize = '24px';
    feedback.style.fontWeight = 'bold';
    feedback.style.pointerEvents = 'none';
    feedback.style.animation = 'floatUp 1s ease-out forwards';
    
    if (delta > 0) {
        feedback.textContent = `+${delta}`;
        feedback.style.color = '#4CAF50';
    } else {
        feedback.textContent = delta;
        feedback.style.color = '#F44336';
    }
    
    // Posicionar cerca del puntaje
    const rect = scoreEl.getBoundingClientRect();
    feedback.style.left = (rect.left + rect.width / 2) + 'px';
    feedback.style.top = rect.top + 'px';
    
    document.body.appendChild(feedback);
    
    // Remover después de la animación
    setTimeout(() => feedback.remove(), 1000);
    
    // Agregar keyframe si no existe
    if (!document.getElementById('floatUp-keyframe')) {
        const style = document.createElement('style');
        style.id = 'floatUp-keyframe';
        style.textContent = `
            @keyframes floatUp {
                0% {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
                100% {
                    opacity: 0;
                    transform: translateY(-50px) scale(1.2);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

function toggleQuickAdjust() {
    const panel = document.getElementById('quick-adjust-panel');
    const isVisible = panel.style.display !== 'none';
    
    if (isVisible) {
        panel.style.display = 'none';
    } else {
        panel.style.display = 'block';
        updateQuickAdjustScores();
    }
}

function updateQuickAdjustScores() {
    const scores = document.querySelectorAll('.score');
    const quickScores = document.querySelectorAll('.player-quick-score');
    
    scores.forEach((scoreEl, idx) => {
        if (quickScores[idx]) {
            quickScores[idx].textContent = scoreEl.textContent;
        }
    });
}

// ===========================
// UI HELPERS
// ===========================

function setStatus(text, variant) {
    // Agregar emojis según el tipo
    let emoji = '';
    if (variant === 'correct') emoji = '✅ ';
    if (variant === 'incorrect') emoji = '❌ ';
    if (variant === 'info') emoji = '💡 ';
    
    elements.statusBar.textContent = emoji + text;
    elements.statusBar.className = variant;
}

function flashStatus(variant, immediateText, afterText) {
    let flashCount = 0;
    const maxFlashes = 6;
    const interval = 150;
    
    elements.statusBar.textContent = immediateText;
    elements.statusBar.className = variant;
    
    const flashInterval = setInterval(() => {
        if (flashCount >= maxFlashes) {
            clearInterval(flashInterval);
            setStatus(afterText, 'info');
            return;
        }
        
        // Toggle entre el color y blanco
        if (flashCount % 2 === 0) {
            elements.statusBar.style.color = 'white';
        } else {
            elements.statusBar.style.color = variant === 'correct' ? 'var(--success)' : 'var(--red)';
        }
        
        flashCount++;
    }, interval);
}

function updateControlsMode() {
    console.log('🎛️ Actualizando controles. Pregunta activa:', gameState.currentQuestion !== null);
    
    // Ocultar todos primero
    elements.boardControls.style.display = 'none';
    elements.panelControls.style.display = 'none';
    elements.moderatorControls.style.display = 'none';
    
    if (gameState.currentQuestion) {
        // Hay pregunta activa
        if (gameState.hideAnswers) {
            console.log('   → Modo: Moderador (respuestas ocultas)');
            elements.moderatorControls.style.display = 'flex';
        } else {
            console.log('   → Modo: Panel (respuestas visibles)');
            elements.panelControls.style.display = 'flex';
        }
    } else {
        // Tablero visible
        console.log('   → Modo: Tablero');
        elements.boardControls.style.display = 'flex';
    }
}

// ===========================
// SONIDOS
// ===========================

function playSound(key) {
    if (sounds[key]) {
        sounds[key].currentTime = 0;
        sounds[key].play().catch(err => console.log('Error reproduciendo sonido:', err));
        
        // Feedback visual según el sonido
        if (key === 'correct') {
            createConfetti();
        } else if (key === 'incorrect') {
            shakeScreen();
        }
    }
}

function createConfetti() {
    // Crear efecto de confetti simple
    for (let i = 0; i < 30; i++) {
        const confetti = document.createElement('div');
        confetti.style.position = 'fixed';
        confetti.style.width = '10px';
        confetti.style.height = '10px';
        confetti.style.backgroundColor = ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1'][Math.floor(Math.random() * 4)];
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.top = '-10px';
        confetti.style.borderRadius = '50%';
        confetti.style.pointerEvents = 'none';
        confetti.style.zIndex = '9999';
        confetti.style.transition = 'all 2s ease-out';
        
        document.body.appendChild(confetti);
        
        setTimeout(() => {
            confetti.style.top = '100vh';
            confetti.style.opacity = '0';
            confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
        }, 10);
        
        setTimeout(() => confetti.remove(), 2000);
    }
}

function shakeScreen() {
    const app = document.getElementById('app');
    app.style.animation = 'shake 0.5s';
    setTimeout(() => {
        app.style.animation = '';
    }, 500);
    
    // Agregar keyframe si no existe
    if (!document.getElementById('shake-keyframe')) {
        const style = document.createElement('style');
        style.id = 'shake-keyframe';
        style.textContent = `
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                20%, 40%, 60%, 80% { transform: translateX(5px); }
            }
        `;
        document.head.appendChild(style);
    }
}

function stopSound(key) {
    if (sounds[key]) {
        sounds[key].pause();
        sounds[key].currentTime = 0;
    }
}

function stopAllSounds() {
    Object.values(sounds).forEach(sound => {
        sound.pause();
        sound.currentTime = 0;
    });
}

// ===========================
// ATAJOS DE TECLADO
// ===========================

document.addEventListener('keydown', (e) => {
    // Números 1-5 para buzzers
    if (e.key >= '1' && e.key <= '5') {
        const playerIdx = parseInt(e.key) - 1;
        const btn = document.querySelectorAll('.buzzer-btn')[playerIdx];
        if (btn && !btn.disabled) {
            pressBuzzer(playerIdx);
        }
        return;
    }
    
    // Solo si hay pregunta activa y respuestas visibles
    if (!gameState.currentQuestion || gameState.hideAnswers) return;
    
    // Letras a-d para seleccionar respuestas
    const key = e.key.toLowerCase();
    if ('abcd'.includes(key)) {
        const index = 'abcd'.indexOf(key);
        selectChoice(index);
        return;
    }
    
    // Enter para enviar respuesta
    if (e.key === 'Enter') {
        submitAnswer();
        return;
    }
    
    // Escape para cancelar
    if (e.key === 'Escape') {
        cancelQuestion();
        return;
    }
});

// ===========================
// INICIALIZACIÓN AL CARGAR
// ===========================

window.addEventListener('load', () => {
    console.log('🎮 Jeopardy Web iniciado');
    
    // Cargar tablero inicial
    fetch('/api/board')
        .then(r => r.json())
        .then(data => {
            renderBoard(data);
            updateScores(data.scores);
        })
        .catch(err => console.error('Error cargando tablero:', err));
});

// Prevenir cierre accidental
window.addEventListener('beforeunload', (e) => {
    if (gameState.currentQuestion) {
        e.preventDefault();
        e.returnValue = '';
    }
});
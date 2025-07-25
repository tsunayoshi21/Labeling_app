// API Service - Maneja todas las llamadas al backend
class APIService {
    static async getCurrentImage() {
        const response = await fetch('/api/current_image');
        return await response.json();
    }

    static async submitCorrection(payload) {
        const response = await fetch('/api/submit_correction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return await response.json();
    }

    static async getStats() {
        const response = await fetch('/api/stats');
        return await response.json();
    }

    static async goToIndex(index) {
        const response = await fetch('/api/go_to_index', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index })
        });
        return await response.json();
    }

    static async saveProgress() {
        const response = await fetch('/api/save_progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return await response.json();
    }
}

// UI Manager - Maneja la interfaz de usuario
class UIManager {
    constructor() {
        this.previousStats = {};
    }

    showLoading(show) {
        const loadingDiv = document.getElementById('loadingDiv');
        const workArea = document.getElementById('workArea');
        
        if (show) {
            loadingDiv.classList.remove('hidden');
            workArea.classList.add('hidden');
        } else {
            loadingDiv.classList.add('hidden');
            workArea.classList.remove('hidden');
        }
    }

    showCompletion(correctedFilePath) {
        document.getElementById('workArea').classList.add('hidden');
        document.getElementById('completionDiv').classList.remove('hidden');
        document.getElementById('correctedFilePath').textContent = correctedFilePath;
    }

    showError(message) {
        const errorDiv = document.getElementById('errorDiv');
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        
        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, 5000);
    }

    showSaveMessage(message, type = 'success') {
        const saveMessage = document.getElementById('saveMessage');
        saveMessage.textContent = message;
        saveMessage.className = `save-message show ${type}`;
        
        setTimeout(() => {
            saveMessage.classList.remove('show');
        }, 3000);
    }

    highlightButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (!button || button.classList.contains('hidden')) return;
        
        button.style.transform = 'scale(1.1)';
        button.style.boxShadow = '0 0 20px rgba(255,255,255,0.8)';
        
        setTimeout(() => {
            button.style.transform = '';
            button.style.boxShadow = '';
        }, 200);
    }

    updateImage(imageData) {
        const imageElement = document.getElementById('currentImage');
        const noImageMessage = document.getElementById('noImageMessage');
        
        if (imageData.image_exists) {
            imageElement.src = `/images/${imageData.image_filename}`;
            imageElement.classList.remove('hidden');
            noImageMessage.classList.add('hidden');
            
            imageElement.onload = function() {
                if (this.naturalWidth < 200 || this.naturalHeight < 100) {
                    this.classList.add('small-image');
                    this.style.minWidth = '400px';
                } else {
                    this.classList.remove('small-image');
                    this.style.minWidth = '';
                }
            };
        } else {
            imageElement.classList.add('hidden');
            noImageMessage.classList.remove('hidden');
        }
    }

    updateProgress(imageData) {
        const progressBar = document.getElementById('progressBar');
        const progress = imageData.progress;
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${progress}%`;
        
        document.getElementById('navInput').max = imageData.total;
        document.getElementById('navInput').value = imageData.current_index + 1;
        
        const prevBtn = document.getElementById('prevBtn');
        if (imageData.current_index <= 0) {
            prevBtn.disabled = true;
            prevBtn.style.opacity = '0.5';
            prevBtn.style.cursor = 'not-allowed';
        } else {
            prevBtn.disabled = false;
            prevBtn.style.opacity = '1';
            prevBtn.style.cursor = 'pointer';
        }
    }

    updateStats(stats) {
        const statsToUpdate = [
            { id: 'totalImages', value: stats.total_original, key: 'total_original' },
            { id: 'reviewedImages', value: stats.reviewed, key: 'reviewed' },
            { id: 'remainingImages', value: stats.remaining, key: 'remaining' },
            { id: 'correctImages', value: stats.correct, key: 'correct' },
            { id: 'editedImages', value: stats.edited, key: 'edited' },
            { id: 'discardedImages', value: stats.discarded, key: 'discarded' }
        ];
        
        statsToUpdate.forEach(stat => {
            const element = document.getElementById(stat.id);
            const statContainer = element.closest('.stat');
            
            if (this.previousStats[stat.key] !== undefined && 
                this.previousStats[stat.key] !== stat.value) {
                
                statContainer.classList.remove('highlight');
                statContainer.offsetHeight;
                statContainer.classList.add('highlight');
                
                setTimeout(() => {
                    statContainer.classList.remove('highlight');
                }, 1000);
            }
            
            element.textContent = stat.value;
        });
        
        document.getElementById('errorRate').textContent = `${stats.error_rate}%`;
        document.getElementById('editRate').textContent = `${stats.edit_rate}%`;
        document.getElementById('discardRate').textContent = `${stats.discard_rate}%`;
        
        this.previousStats = {
            total_original: stats.total_original,
            reviewed: stats.reviewed,
            remaining: stats.remaining,
            correct: stats.correct,
            edited: stats.edited,
            discarded: stats.discarded
        };
    }
}

// Edit Mode Manager - Maneja el modo de edición
class EditModeManager {
    constructor() {
        this.isEditMode = false;
    }

    toggleEditMode(transcription) {
        this.isEditMode = true;
        const transcriptionDisplay = document.getElementById('transcriptionDisplay');
        const editInput = document.getElementById('editInput');
        const correctBtn = document.getElementById('correctBtn');
        const editBtn = document.getElementById('editBtn');
        const discardBtn = document.getElementById('discardBtn');
        const saveEditBtn = document.getElementById('saveEditBtn');
        const cancelBtn = document.getElementById('cancelBtn');
        
        transcriptionDisplay.classList.add('hidden');
        editInput.classList.remove('hidden');
        editInput.value = transcription;
        editInput.focus();
        editInput.select();
        
        correctBtn.classList.add('hidden');
        editBtn.classList.add('hidden');
        discardBtn.classList.add('hidden');
        saveEditBtn.classList.remove('hidden');
        cancelBtn.classList.remove('hidden');
    }

    cancelEdit() {
        this.isEditMode = false;
        const transcriptionDisplay = document.getElementById('transcriptionDisplay');
        const editInput = document.getElementById('editInput');
        const correctBtn = document.getElementById('correctBtn');
        const editBtn = document.getElementById('editBtn');
        const discardBtn = document.getElementById('discardBtn');
        const saveEditBtn = document.getElementById('saveEditBtn');
        const cancelBtn = document.getElementById('cancelBtn');
        
        transcriptionDisplay.classList.remove('hidden');
        editInput.classList.add('hidden');
        
        correctBtn.classList.remove('hidden');
        editBtn.classList.remove('hidden');
        discardBtn.classList.remove('hidden');
        saveEditBtn.classList.add('hidden');
        cancelBtn.classList.add('hidden');
    }

    getEditedText() {
        return document.getElementById('editInput').value.trim();
    }
}

// Keyboard Handler - Maneja los atajos de teclado
class KeyboardHandler {
    constructor(appController) {
        this.appController = appController;
        this.setupKeyboardListeners();
    }

    setupKeyboardListeners() {
        document.addEventListener('keydown', (e) => {
            if (this.appController.editModeManager.isEditMode) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.appController.saveEdit();
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    this.appController.cancelEdit();
                }
                return;
            }
            
            switch(e.key) {
                case '1':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('correctBtn');
                    this.appController.submitAction('correct');
                    break;
                case '2':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('editBtn');
                    this.appController.toggleEditMode();
                    break;
                case '3':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('discardBtn');
                    this.appController.submitAction('discard');
                    break;
                case 'ArrowRight':
                case ' ':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('correctBtn');
                    this.appController.submitAction('correct');
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.appController.goToPreviousImage();
                    break;
                case 'Delete':
                case 'Backspace':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('discardBtn');
                    this.appController.submitAction('discard');
                    break;
                case 'e':
                case 'E':
                    e.preventDefault();
                    this.appController.uiManager.highlightButton('editBtn');
                    this.appController.toggleEditMode();
                    break;
                case 's':
                case 'S':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.appController.manualSaveProgress();
                    }
                    break;
            }
        });
    }
}

// App Controller - Controlador principal de la aplicación
class AppController {
    constructor() {
        this.currentImageData = null;
        this.uiManager = new UIManager();
        this.editModeManager = new EditModeManager();
        this.keyboardHandler = new KeyboardHandler(this);
        
        this.init();
    }

    async init() {
        await this.loadCurrentImage();
        await this.updateStats();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('correctBtn').addEventListener('click', () => this.submitAction('correct'));
        document.getElementById('editBtn').addEventListener('click', () => this.toggleEditMode());
        document.getElementById('discardBtn').addEventListener('click', () => this.submitAction('discard'));
        document.getElementById('saveEditBtn').addEventListener('click', () => this.saveEdit());
        document.getElementById('cancelBtn').addEventListener('click', () => this.cancelEdit());
        document.getElementById('navBtn').addEventListener('click', () => this.navigateToImage());
        document.getElementById('prevBtn').addEventListener('click', () => this.goToPreviousImage());
        document.getElementById('saveBtn').addEventListener('click', () => this.manualSaveProgress());
        
        document.getElementById('editInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.saveEdit();
            }
        });
        
        document.getElementById('navInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.navigateToImage();
            }
        });
    }

    async loadCurrentImage() {
        try {
            this.uiManager.showLoading(true);
            const data = await APIService.getCurrentImage();
            
            if (data.finished) {
                this.uiManager.showCompletion(data.corrected_file);
                return;
            }
            
            this.currentImageData = data;
            this.updateUI();
            this.uiManager.showLoading(false);
            
            window.scrollTo(0, 0);
            
        } catch (error) {
            console.error('Error loading image:', error);
            this.uiManager.showError('Error al cargar la imagen');
            this.uiManager.showLoading(false);
        }
    }

    updateUI() {
        if (!this.currentImageData) return;
        
        this.uiManager.updateImage(this.currentImageData);
        this.uiManager.updateProgress(this.currentImageData);
        
        document.getElementById('transcriptionDisplay').textContent = this.currentImageData.transcription;
    }

    async updateStats() {
        try {
            const stats = await APIService.getStats();
            this.uiManager.updateStats(stats);
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    async submitAction(action) {
        if (!this.currentImageData) return;
        
        try {
            const payload = {
                action: action,
                image_key: this.currentImageData.image_key
            };
            
            const result = await APIService.submitCorrection(payload);
            
            if (result.success) {
                await this.loadCurrentImage();
                await this.updateStats();
            } else {
                this.uiManager.showError(result.error || 'Error al procesar la acción');
            }
            
        } catch (error) {
            console.error('Error submitting action:', error);
            this.uiManager.showError('Error al enviar la acción');
        }
    }

    toggleEditMode() {
        this.editModeManager.toggleEditMode(this.currentImageData.transcription);
    }

    async saveEdit() {
        const newTranscription = this.editModeManager.getEditedText();
        
        if (!newTranscription) {
            this.uiManager.showError('La transcripción no puede estar vacía');
            return;
        }
        
        try {
            const payload = {
                action: 'edit',
                image_key: this.currentImageData.image_key,
                new_transcription: newTranscription
            };
            
            const result = await APIService.submitCorrection(payload);
            
            if (result.success) {
                this.cancelEdit();
                await this.loadCurrentImage();
                await this.updateStats();
            } else {
                this.uiManager.showError(result.error || 'Error al guardar la edición');
            }
            
        } catch (error) {
            console.error('Error saving edit:', error);
            this.uiManager.showError('Error al guardar la edición');
        }
    }

    cancelEdit() {
        this.editModeManager.cancelEdit();
    }

    async navigateToImage() {
        const navInput = document.getElementById('navInput');
        const targetIndex = parseInt(navInput.value) - 1;
        
        if (isNaN(targetIndex) || targetIndex < 0) {
            this.uiManager.showError('Índice inválido');
            return;
        }
        
        try {
            const result = await APIService.goToIndex(targetIndex);
            
            if (result.success) {
                await this.loadCurrentImage();
                await this.updateStats();
            } else {
                this.uiManager.showError(result.error || 'Error al navegar');
            }
            
        } catch (error) {
            console.error('Error navigating:', error);
            this.uiManager.showError('Error al navegar');
        }
    }

    async goToPreviousImage() {
        if (!this.currentImageData || this.currentImageData.current_index <= 0) {
            this.uiManager.showError('Ya estás en la primera imagen');
            return;
        }
        
        const targetIndex = this.currentImageData.current_index - 1;
        
        try {
            const result = await APIService.goToIndex(targetIndex);
            
            if (result.success) {
                await this.loadCurrentImage();
                await this.updateStats();
            } else {
                this.uiManager.showError(result.error || 'Error al retroceder');
            }
            
        } catch (error) {
            console.error('Error going to previous image:', error);
            this.uiManager.showError('Error al retroceder');
        }
    }

    async manualSaveProgress() {
        try {
            const saveBtn = document.getElementById('saveBtn');
            const originalText = saveBtn.innerHTML;
            saveBtn.innerHTML = '⏳ Guardando...';
            saveBtn.disabled = true;
            
            const result = await APIService.saveProgress();
            
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            
            if (result.success) {
                this.uiManager.showSaveMessage(`✅ ${result.message} (${result.timestamp})`, 'success');
            } else {
                this.uiManager.showSaveMessage(`❌ ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error saving progress:', error);
            const saveBtn = document.getElementById('saveBtn');
            saveBtn.innerHTML = '💾 Guardar';
            saveBtn.disabled = false;
            this.uiManager.showSaveMessage('❌ Error al guardar el progreso', 'error');
        }
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    new AppController();
});

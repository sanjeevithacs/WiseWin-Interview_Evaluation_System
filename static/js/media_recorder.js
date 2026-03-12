class InterviewMediaRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.stream = null;
        this.chunks = [];
        this.blob = null;
        this.blobUrl = null;
        this.mimeType = null;
        this.isRecording = false;
        this.startTime = null;
        this.duration = 0;
        this.timerInterval = null;
        this.stopResolver = null;
        this.stopRejecter = null;
        this.autoStopTimeout = null;
    }

    getSupportedMimeType() {
        const mimeTypes = [
            'video/webm;codecs=vp9,opus',
            'video/webm;codecs=vp8,opus',
            'video/webm;codecs=h264,opus',
            'video/webm'
        ];

        for (const candidate of mimeTypes) {
            if (window.MediaRecorder && typeof MediaRecorder.isTypeSupported === 'function' && MediaRecorder.isTypeSupported(candidate)) {
                return candidate;
            }
        }

        return 'video/webm';
    }

    async startRecording({ maxDuration = 120 } = {}) {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('getUserMedia is not supported in this browser.');
        }
        if (!window.MediaRecorder) {
            throw new Error('MediaRecorder is not supported in this browser.');
        }
        if (this.isRecording) {
            return;
        }

        this.cleanupBlobUrl();
        this.chunks = [];
        this.blob = null;
        this.duration = 0;
        this.startTime = Date.now();
        this.mimeType = this.getSupportedMimeType();

        this.stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 30, max: 30 }
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        this.mediaRecorder = new MediaRecorder(this.stream, { mimeType: this.mimeType });
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                this.chunks.push(event.data);
            }
        };

        this.mediaRecorder.onstop = async () => {
            this.stopTimer();
            this.clearAutoStop();
            this.duration = Math.max(this.duration, Math.round((Date.now() - this.startTime) / 1000));
            this.blob = new Blob(this.chunks, { type: this.mediaRecorder.mimeType || this.mimeType || 'video/webm' });
            this.blobUrl = URL.createObjectURL(this.blob);
            const result = {
                blob: this.blob,
                blobUrl: this.blobUrl,
                duration: this.duration,
                mimeType: this.blob.type || this.mimeType || 'video/webm'
            };
            if (typeof this.onRecordingComplete === 'function') {
                await this.onRecordingComplete(result);
            }
            this.stopTracks();
            if (this.stopResolver) {
                this.stopResolver(result);
                this.stopResolver = null;
            }
            this.stopRejecter = null;
        };

        this.mediaRecorder.onerror = (event) => {
            const recorderError = event?.error || new Error('Recording failed.');
            if (this.stopRejecter) {
                this.stopRejecter(recorderError);
            }
            this.stopResolver = null;
            this.stopRejecter = null;
            this.stopTracks();
            this.stopTimer();
            this.clearAutoStop();
        };

        this.mediaRecorder.start(1000);
        this.isRecording = true;
        this.startTimer();
        this.setAutoStop(maxDuration);
    }

    stopRecording() {
        if (!this.mediaRecorder || !this.isRecording) {
            return Promise.resolve(null);
        }

        this.isRecording = false;
        return new Promise((resolve, reject) => {
            this.stopResolver = resolve;
            this.stopRejecter = reject;
            this.mediaRecorder.stop();
        });
    }

    setAutoStop(maxDuration) {
        this.clearAutoStop();
        this.autoStopTimeout = setTimeout(() => {
            if (this.isRecording) {
                this.stopRecording();
            }
        }, maxDuration * 1000);
    }

    clearAutoStop() {
        if (this.autoStopTimeout) {
            clearTimeout(this.autoStopTimeout);
            this.autoStopTimeout = null;
        }
    }

    startTimer() {
        this.stopTimer();
        this.timerInterval = setInterval(() => {
            this.duration = Math.round((Date.now() - this.startTime) / 1000);
            if (typeof this.onTimerUpdate === 'function') {
                this.onTimerUpdate(this.duration);
            }
        }, 250);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    stopTracks() {
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
    }

    cleanupBlobUrl() {
        if (this.blobUrl) {
            URL.revokeObjectURL(this.blobUrl);
            this.blobUrl = null;
        }
    }

    reset() {
        this.stopTracks();
        this.stopTimer();
        this.clearAutoStop();
        this.cleanupBlobUrl();
        this.mediaRecorder = null;
        this.chunks = [];
        this.blob = null;
        this.isRecording = false;
        this.duration = 0;
    }
}

window.InterviewMediaRecorder = InterviewMediaRecorder;

/**
 * Enhanced MediaRecorder with proper video handling
 * Fixes all recording and playback issues
 */

class EnhancedInterviewMediaRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.videoChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.recordingType = null;
        this.startTime = null;
        this.duration = 0;
        this.timerInterval = null;
        this.autoStopTimeout = null;
        this.blobUrl = null;
    }

    async startRecording(type = 'video', constraints = {}, maxDuration = 120) {
        try {
            // Check browser compatibility
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Browser does not support media recording. Please use Chrome, Firefox, or Edge.');
            }

            if (!window.MediaRecorder) {
                throw new Error('MediaRecorder API is not supported in this browser.');
            }

            this.recordingType = type;
            this.audioChunks = [];
            this.videoChunks = [];
            this.startTime = Date.now();

            // Enhanced constraints for better video quality
            const defaultConstraints = {
                video: {
                    width: { ideal: 1280, max: 1920 },
                    height: { ideal: 720, max: 1080 },
                    facingMode: 'user',
                    frameRate: { ideal: 30, max: 60 }
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                }
            };

            // Merge with custom constraints
            const finalConstraints = type === 'video' ? 
                { ...defaultConstraints, ...constraints } : 
                { audio: defaultConstraints.audio, ...constraints };

            // Get media stream
            this.stream = await navigator.mediaDevices.getUserMedia(finalConstraints);

            // Create MediaRecorder with proper MIME type
            let mimeType = 'video/webm;codecs=vp9';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'video/webm;codecs=vp8';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'video/webm';
                }
            }

            this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });

            // Set up event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    if (type === 'audio') {
                        this.audioChunks.push(event.data);
                    } else {
                        this.videoChunks.push(event.data);
                    }
                }
            };

            this.mediaRecorder.onstop = () => {
                this.stopTimer();
                this.clearAutoStop();
                this.processRecording();
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('MediaRecorder error:', event.error);
                this.onError(event.error);
            };

            // Start recording with smaller chunks for better quality
            this.mediaRecorder.start(1000); // Collect data every 1 second
            this.isRecording = true;
            this.startTimer();
            
            // Set auto-stop timer
            this.setAutoStop(maxDuration);

            return true;
        } catch (error) {
            console.error('Error starting recording:', error);
            this.onError(error);
            return false;
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop all tracks
            if (this.stream) {
                this.stream.getTracks().forEach(track => {
                    track.stop();
                });
            }
        }
    }

    setAutoStop(maxDuration) {
        this.clearAutoStop();
        this.autoStopTimeout = setTimeout(() => {
            if (this.isRecording) {
                console.log(`Auto-stopping recording after ${maxDuration} seconds`);
                this.stopRecording();
                this.onAutoStop(maxDuration);
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
        this.timerInterval = setInterval(() => {
            this.duration = Math.floor((Date.now() - this.startTime) / 1000);
            this.onTimerUpdate(this.duration);
        }, 100);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    async processRecording() {
        try {
            let audioBlob = null;
            let videoBlob = null;

            // Create blobs with proper MIME type
            const mimeType = this.recordingType === 'video' ? 'video/webm' : 'audio/webm';

            if (this.recordingType === 'audio' && this.audioChunks.length > 0) {
                audioBlob = new Blob(this.audioChunks, { type: mimeType });
            } else if (this.recordingType === 'video' && this.videoChunks.length > 0) {
                videoBlob = new Blob(this.videoChunks, { type: mimeType });
            }

            // Create Blob URL for immediate playback
            if (videoBlob) {
                this.blobUrl = URL.createObjectURL(videoBlob);
            }

            // Convert to base64 for storage
            const result = {
                audioBase64: audioBlob ? await this.blobToBase64(audioBlob) : null,
                videoBase64: videoBlob ? await this.blobToBase64(videoBlob) : null,
                videoBlobUrl: this.blobUrl,
                duration: this.duration,
                type: this.recordingType,
                mimeType: mimeType,
                timestamp: new Date().toISOString()
            };

            this.onRecordingComplete(result);
        } catch (error) {
            console.error('Error processing recording:', error);
            this.onError(error);
        }
    }

    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

    // Get recording for immediate playback
    getRecordingForPlayback() {
        return {
            blobUrl: this.blobUrl,
            duration: this.duration,
            type: this.recordingType
        };
    }

    // Cleanup resources
    cleanup() {
        this.stopRecording();
        this.clearAutoStop();
        if (this.blobUrl) {
            URL.revokeObjectURL(this.blobUrl);
            this.blobUrl = null;
        }
    }

    // Event callbacks (to be overridden)
    onTimerUpdate(duration) {
        // Override in implementation
    }

    onRecordingComplete(result) {
        // Override in implementation
    }

    onError(error) {
        // Override in implementation
    }

    onAutoStop(maxDuration) {
        // Override in implementation
    }
}

// Export for use in main script
window.EnhancedInterviewMediaRecorder = EnhancedInterviewMediaRecorder;

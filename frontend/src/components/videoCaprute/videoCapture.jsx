import React, { useState, useEffect, useRef } from 'react';
import './videocapture.css';
import classnames from "classnames"

const VideoCaptureComponent = ({ onSendHandler, response, setResponse }) => {
    const [videoStream, setVideoStream] = useState(null);
    const [photo, setPhoto] = useState(null);
    const [isCapturing, setIsCapturing] = useState(true);
    const videoRef = useRef(null);
    const canvasRef = useRef(null);

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            setVideoStream(stream);
        } catch (error) {
            console.error('Ошибка при получении доступа к камере:', error);
        }
    };

    useEffect(() => {
        startCamera();

        return () => {
            if (videoStream) {
                videoStream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    useEffect(() => {
        if (videoStream && videoRef.current) {
            videoRef.current.srcObject = videoStream;
        }
    }, [videoStream]);

    const capturePhoto = () => {
        if (canvasRef.current && videoRef.current) {
            const canvas = canvasRef.current;
            const video = videoRef.current;

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            const photoData = canvas.toDataURL('image/png');
            setPhoto(photoData);
            setIsCapturing(false);
        }
    };

    const retakePhoto = () => {
        setPhoto(null);
        setIsCapturing(true);
        setResponse("")

        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
        }
        startCamera();
    };

    const sendPhoto = async () => {
        try {
            onSendHandler(photo)
        } catch (error) {
            console.error('Ошибка при отправке данных:', error);
        }
    };

    return (
        <div>
            {isCapturing ? (
                <>
                    <div className="video-capture-container">
                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            className="video-element"
                        />
                    </div>
                    <button onClick={capturePhoto} className="capture-button">
                        Сделать фото
                    </button>
                </>
            ) : (
                <>
                    <div className={classnames("video-capture-container photo", {"error": response=="error"})}>
                        <img src={photo} alt="Фото" className="photo-element" />
                    </div>
                    <div className="button-container">
                        <button onClick={retakePhoto} className="retake-button">
                            Переделать
                        </button>
                        <button onClick={sendPhoto} className="send-button">
                            Отправить
                        </button>
                    </div>
                </>
            )}
            <canvas ref={canvasRef} className="hidden-canvas" />
        </div>
    );
};

export default VideoCaptureComponent;
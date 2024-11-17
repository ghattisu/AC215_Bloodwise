'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, DescriptionOutlined } from '@mui/icons-material';
import IconButton from '@mui/material/IconButton';
import { parse } from 'papaparse';

// Styles
import styles from './ChatInput.module.css';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';

export default function ChatInput({
    onSendMessage,
    selectedModel,
    onModelChange,
    disableModelSelect = false
}) {
    // Component States
    const [message, setMessage] = useState('');
    // const [selectedImage, setSelectedImage] = useState(null);
    const [selectedFile, setSelectedFile] = useState(null);
    const textAreaRef = useRef(null);
    const fileInputRef = useRef(null);

    const adjustTextAreaHeight = () => {
        const textarea = textAreaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = `${textarea.scrollHeight}px`;
        }
    };

    // Setup Component
    useEffect(() => {
        adjustTextAreaHeight();
    }, [message]);

    // Handlers
    const handleMessageChange = (e) => {
        setMessage(e.target.value);
    };
    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            if (e.shiftKey) {
                // Shift + Enter: add new line
                return;
            } else {
                // Enter only: submit
                e.preventDefault();
                handleSubmit();
            }
        }
    };
    const handleSubmit = () => {

        if (message.trim() || selectedFile) {
            console.log('Submitting message:', message);
            const newMessage = {
                content: message.trim(),
                // image: selectedImage?.preview || null
                file: selectedFile || null,
            };

            // Send the message
            onSendMessage(newMessage);

            // Reset
            setMessage('');
            // setSelectedImage(null);
            setSelectedFile(null);
            if (textAreaRef.current) {
                textAreaRef.current.style.height = 'auto';
            }
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };
    const handleFileClick = () => {
        fileInputRef.current?.click();
    };
    const handleFileChange = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > 5000000) { // 5MB limit
                alert('File size should be less than 5MB');
                return;
            }

            parse(file, {
                complete: (results) => {
                    setSelectedFile(results.data);
                    // setSelectedFile({
                    //     file: file,
                    //     data: results.data
                    // });
                },
                header: true,
                skipEmptyLines: true,
            });

            // const reader = new FileReader();
            // reader.onloadend = () => {
            //     // setSelectedImage({
            //     //     file: file,
            //     //     preview: reader.result
            //     // });
            //     setSelectedFile(file);
            // };
            // // reader.readAsDataURL(file);
            // reader.readAsText(file)
        }
    };
    const handleModelChange = (event) => {
        onModelChange(event.target.value);
    };

    // const removeImage = () => {
    //     setSelectedImage(null);
    //     if (fileInputRef.current) {
    //         fileInputRef.current.value = '';
    //     }
    // };
    const removeFile = () => {
        setSelectedFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className={styles.chatInputContainer}>
            {selectedFile && (
                <div className={styles.filePreview}>
                    <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                        <TableRow>
                            {Object.keys(selectedFile[0]).map((header) => (
                            <TableCell key={header}>{header}</TableCell>
                            ))}
                        </TableRow>
                        </TableHead>
                        <TableBody>
                        {selectedFile.map((row, idx) => (
                            <TableRow key={idx}>
                            {Object.keys(row).map((cell, i) => (
                                <TableCell key={i}>{row[cell]}</TableCell>
                            ))}
                            </TableRow>
                        ))}
                        </TableBody>
                    </Table>
                    </TableContainer>

                    <button
                        className={styles.removeFileBtn}
                        onClick={removeFile}
                    >
                        ×
                    </button>
                </div>
            )}


            <div className={styles.textareaWrapper}>
                <textarea
                    ref={textAreaRef}
                    className={styles.chatInput}
                    placeholder="How can Bloodwise help you today?"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit();
                        }
                    }}
                    rows={1}
                />
                <button
                    className={`${styles.submitButton} ${message.trim() ? styles.active : ''}`}
                    onClick={handleSubmit}
                    // disabled={!message.trim() && !selectedImage}
                    disabled={!message.trim() && !selectedFile}
                >
                    <Send />
                </button>
            </div>
            <div className={styles.inputControls}>
                <div className={styles.leftControls}>
                    <input
                        type="file"
                        ref={fileInputRef}
                        className={styles.hiddenFileInput}
                        accept="text/"
                        onChange={handleFileChange}
                    />
                    <IconButton aria-label="dataset" className={styles.iconButton} onClick={handleFileClick}>
                        <DescriptionOutlined />
                    </IconButton>
                </div>
            </div>
        </div>
    )
}
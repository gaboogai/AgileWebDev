async function sendSongToServer(songData) {
    try {
        const response = await fetch('/process_ajax', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(songData)
        });
        
        const result = await response.json();
        console.log('Server response:', result);
        return result;
    } catch (error) {
        console.error('Error sending song to server:', error);
        throw error;
    }
}
// Debug script to check button states
(function() {
    const stopButton = document.querySelector('button[data-testid="stop-button"]');
    const voiceButton = document.querySelector('button[data-testid="composer-speech-button"]');
    const sendButton = document.querySelector('button[data-testid="composer-send-button"]');
    
    console.log('=== Button Detection Debug ===');
    console.log('Stop button:', stopButton ? 'FOUND' : 'NOT FOUND');
    console.log('Voice button:', voiceButton ? 'FOUND' : 'NOT FOUND');
    console.log('Send button:', sendButton ? 'FOUND' : 'NOT FOUND');
    
    // Try to find all buttons and log them
    const allButtons = document.querySelectorAll('button');
    console.log(`Total buttons found: ${allButtons.length}`);
    
    // Log buttons with data-testid
    allButtons.forEach((btn, index) => {
        const testId = btn.getAttribute('data-testid');
        if (testId) {
            console.log(`Button ${index}: data-testid="${testId}"`);
        }
    });
    
    return {
        stopButton: !!stopButton,
        voiceButton: !!voiceButton,
        sendButton: !!sendButton,
        totalButtons: allButtons.length
    };
})();


document.addEventListener('DOMContentLoaded', function() {
    // Animate messages in from right
    function showMessages() {
        const messages = document.querySelectorAll('.alert-message, .app-message');
        
        messages.forEach((msg, index) => {
            setTimeout(() => {
                msg.classList.add('show');
                
                // Auto-dismiss after 5 seconds
                setTimeout(() => {
                    dismissMessage(msg);
                }, 5000);
            }, index * 200); // Staggered appearance
        });
    }
    
    // Dismiss message with animation to right
    function dismissMessage(element) {
        element.style.transform = 'translateX(120%)';
        element.style.opacity = '0';
        
        setTimeout(() => {
            element.remove();
        }, 500);
    }
    
    // Close button event
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('close-message')) {
            const message = e.target.closest('.alert-message, .app-message');
            dismissMessage(message);
        }
    });
    
    // Initialize
    showMessages();
});
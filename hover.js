// Check if the browser supports speech synthesis
if ('speechSynthesis' in window) {
  let isReaderEnabled = false; // Track the state of the screen reader
  const synth = window.speechSynthesis; // Speech synthesis API

  // Function to read text content
  const readText = (text) => {
    if (text && text.trim() !== "") {
      synth.cancel(); // Stop any ongoing speech before starting new
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1; // Adjust speaking rate (0.1 to 10)
      utterance.pitch = 1; // Adjust pitch (0 to 2)
      utterance.volume = 1; // Adjust volume (0 to 1)
      synth.speak(utterance);
    }
  };

  // Function to toggle the screen reader
  const toggleScreenReader = () => {
    isReaderEnabled = !isReaderEnabled;
    alert(`Screen Reader ${isReaderEnabled ? 'Enabled' : 'Disabled'}`);
    if (!isReaderEnabled) {
      synth.cancel(); // Stop any ongoing speech
    }
  };

  // Listen for a specific keyboard shortcut (e.g., Shift+R)
  document.addEventListener('keydown', (event) => {
    if (event.shiftKey && event.key.toLowerCase() === 'r') {
      toggleScreenReader();
    }
  });

  // Function to read text or alt of the hovered element
  const getElementText = (el) => {
    if (el.tagName === 'IMG' && el.alt) {
      return el.alt; // If it's an image, read the alt text
    }
    return el.textContent || el.innerText; // Otherwise, read the text content
  };

  // Add hover functionality for all elements
  const readableElements = document.querySelectorAll('body *');
  readableElements.forEach((el) => {
    el.addEventListener('mouseenter', (e) => {
      if (isReaderEnabled) {
        // Read only the content of the hovered element
        const text = getElementText(el);
        if (text) {
          readText(text);
        }
        e.stopPropagation(); // Prevent reading parent elements
      }
    });

    el.addEventListener('mouseleave', () => {
      if (isReaderEnabled) {
        synth.cancel(); // Stop reading when the mouse leaves the element
      }
    });
  });

  // MutationObserver to handle dynamically added elements
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) { // Ensure the node is an element
            const text = getElementText(node);
            if (text && isReaderEnabled) {
              readText(text);
            }

            // Add hover functionality to new elements
            node.addEventListener('mouseenter', (e) => {
              if (isReaderEnabled) {
                const text = getElementText(node);
                if (text) {
                  readText(text);
                }
                e.stopPropagation(); // Prevent reading parent elements
              }
            });

            node.addEventListener('mouseleave', () => {
              if (isReaderEnabled) {
                synth.cancel();
              }
            });
          }
        });
      }
    });
  });

  // Observe changes in the document body
  observer.observe(document.body, { childList: true, subtree: true });
} else {
  console.error('Screen Reader Not Supported in this browser.');
}

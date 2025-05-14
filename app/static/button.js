var toggle = false;
function toggleText() {
toggle = !toggle;
let text;
if (toggle) {
text = "You pressed the button!";
} else {
text = "";
}
document.getElementById("textBox").innerHTML = text;

fetch('/search-suggestions', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      url: `/search?q=${encodeURIComponent('your search term')}`
    })
    .then(response => response.text())
    .then(data => {
      console.log('Search results:', data);
    })
    .catch(error => {
      console.error('AJAX error:', error);
    });
}

// Add auto-complete functionality
function setupAutoComplete() {
  const searchInput = document.querySelector('input[name="q"]');
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.id = 'suggestions';
    suggestionsDiv.className = 'suggestions-container';
    searchInput.parentNode.appendChild(suggestionsDiv);
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value;
        
        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Set new timeout to prevent too many requests
        searchTimeout = setTimeout(() => {
            if (query.length > 0) {
                // Show loading indicator
                suggestionsDiv.innerHTML = '<div class="loading">Searching...</div>';
                
                // Make AJAX request
                const xhr = new XMLHttpRequest();
                xhr.open('GET', `/search-suggestions?q=${encodeURIComponent(query)}`, true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        const data = JSON.parse(xhr.responseText);
                        suggestionsDiv.innerHTML = '';
                        
                        if (data.suggestions.length === 0) {
                            suggestionsDiv.innerHTML = '<div class="no-results">No matches found</div>';
                            return;
                        }
                        
                        data.suggestions.forEach(suggestion => {
                            const div = document.createElement('div');
                            div.className = 'suggestion-item';
                            div.textContent = `${suggestion.title} - ${suggestion.artist}`;
                            div.addEventListener('click', () => {
                                searchInput.value = `${suggestion.title} - ${suggestion.artist}`;
                                suggestionsDiv.innerHTML = '';
                            });
                            suggestionsDiv.appendChild(div);
                        });
                    } else {
                        suggestionsDiv.innerHTML = '<div class="error">Error loading suggestions</div>';
                    }
                };
                
                xhr.onerror = function() {
                    suggestionsDiv.innerHTML = '<div class="error">Error loading suggestions</div>';
                };
                
                xhr.send();
            } else {
                suggestionsDiv.innerHTML = '';
            }
        }, 300); // 300ms delay
    });
}

document.addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
  event.preventDefault();
  document.getElementById("myButton").click();
  }
  });

// Initialize auto-complete when the page loads
document.addEventListener('DOMContentLoaded', setupAutoComplete);
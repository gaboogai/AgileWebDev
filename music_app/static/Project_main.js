const uploadForm = document.getElementById('uploadForm');
    const songsList = document.getElementById('songsList');
    const titleSuggestions = document.getElementById('titleSuggestions');
    const artistSuggestions = document.getElementById('artistSuggestions');

    let uploadedSongs = [];

    function showSuggestions(field) {
      const input = document.getElementById(field);
      const suggestionsDiv = field === 'title' ? titleSuggestions : artistSuggestions;
      suggestionsDiv.innerHTML = '';

      const searchText = input.value.trim().toLowerCase();
      if (searchText === '') return;

      let suggestions = [];
      if (field === 'title') {
        suggestions = uploadedSongs.map(song => song.title).filter(title => title.toLowerCase().includes(searchText));
      } else if (field === 'artist') {
        suggestions = uploadedSongs.map(song => song.artist).filter(artist => artist.toLowerCase().includes(searchText));
      }

      suggestions.forEach(suggestion => {
        const suggestionElement = document.createElement('div');
        suggestionElement.textContent = suggestion;
        suggestionElement.onclick = function() {
          input.value = suggestion;
          suggestionsDiv.innerHTML = ''; 
        };
        suggestionsDiv.appendChild(suggestionElement);
      });
    }

    function renderSongs() {
      songsList.innerHTML = ''; 
      uploadedSongs.forEach(song => {
        const songCard = document.createElement('div');
        songCard.className = 'song-card';

        const titleElement = document.createElement('p');
        titleElement.innerHTML = `<strong>Title:</strong> ${song.title}`;

        const artistElement = document.createElement('p');
        artistElement.innerHTML = `<strong>Artist:</strong> ${song.artist}`;

        const starsElement = document.createElement('div');
        starsElement.className = 'stars';
        starsElement.innerHTML = `
          <span class="star" data-value="1">&#9733;</span>
          <span class="star" data-value="2">&#9733;</span>
          <span class="star" data-value="3">&#9733;</span>
          <span class="star" data-value="4">&#9733;</span>
          <span class="star" data-value="5">&#9733;</span>
        `;
        
        starsElement.addEventListener('click', function(event) {
          if (event.target.classList.contains('star')) {
            const rating = event.target.getAttribute('data-value');
            song.rating = rating;
            updateStars(songCard, rating);
          }
        });

        updateStars(songCard, song.rating);

        
        const commentSection = document.createElement('div');
        commentSection.className = 'comment-section';
        const commentInput = document.createElement('textarea');
        commentInput.placeholder = 'Leave a comment about this song...';
        commentInput.rows = 4;
        commentInput.oninput = function() {
          song.comment = commentInput.value;  
        };

        commentSection.appendChild(commentInput);

        songCard.appendChild(titleElement);
        songCard.appendChild(artistElement);
        songCard.appendChild(starsElement);
        songCard.appendChild(commentSection);

        songsList.appendChild(songCard);
      });
    }

    function updateStars(songCard, rating) {
      const stars = songCard.querySelectorAll('.star');
      stars.forEach(star => {
        star.classList.remove('selected');
      });
      for (let i = 0; i < rating; i++) {
        stars[i].classList.add('selected');
      }
    }

    uploadForm.addEventListener('submit', function(event) {
      event.preventDefault();

      const title = document.getElementById('title').value.trim();
      const artist = document.getElementById('artist').value.trim();

      if (!title || !artist) {
        alert('Please fill in both title and artist.');
        return;
      }

      
      const lastSong = uploadedSongs[uploadedSongs.length - 1];
      if (lastSong && !lastSong.comment) {
        alert('Please leave a comment for the previous song before uploading a new one.');
        return;
      }

      
      uploadedSongs = [];  

      
      const newSong = {
        id: Date.now(),
        title: title,
        artist: artist,
        rating: 0,
        comment: ''  
      };

      uploadedSongs.push(newSong);

      renderSongs();  
    });


const uploadForm = document.getElementById('uploadForm');
const uploadBtn = document.getElementById('uploadBtn');
const requiredFields = ['title', 'artist', 'cover', 'audio'];

uploadForm.addEventListener('input', () => {
  let allFilled = requiredFields.every(id => {
    const el = document.getElementById(id);
    return el && el.value;
  });
  uploadBtn.disabled = !allFilled;
});

uploadForm.addEventListener('submit', function(event) {
  event.preventDefault();

  // Show "Publishing..." message
  const publishingMessage = document.createElement('p');
  publishingMessage.textContent = 'Publishing your song...';
  uploadForm.appendChild(publishingMessage);

  uploadBtn.disabled = true; // Disable button during "publishing"

  // Simulate upload delay
  setTimeout(() => {
    publishingMessage.remove(); // Remove publishing message
    alert('✅ Music uploaded successfully!');
    uploadForm.reset();
    uploadBtn.disabled = true;
  }, 2000); // 2 seconds
});


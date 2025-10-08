const askBtn = document.getElementById('askBtn');
const queryInput = document.getElementById('query');
const answerDiv = document.getElementById('answer');
const metaDiv = document.getElementById('meta');
const askStatus = document.getElementById('askStatus');

const uploadBtn = document.getElementById('uploadBtn');
const pdfInput = document.getElementById('pdf');
const uploadStatus = document.getElementById('uploadStatus');

askBtn.addEventListener('click', async () => {
  const query = queryInput.value.trim();
  if (!query) {
    askStatus.textContent = 'Please enter a query.';
    return;
  }
  askStatus.textContent = 'Thinking...';
  answerDiv.textContent = '';
  metaDiv.textContent = '';

  try {
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    if (!res.ok) throw new Error('Request failed');
    const data = await res.json();
    answerDiv.textContent = data.answer || '(no answer)';
    
    // Format metadata with better structure
    const agentsText = `Agents used: ${data.agents_used?.join(', ') || 'N/A'}`;
    const rationaleText = `Rationale: ${data.rationale || 'No rationale provided'}`;
    metaDiv.textContent = `${agentsText}\n\n${rationaleText}`;
    
    askStatus.textContent = '';
  } catch (e) {
    askStatus.textContent = 'Error: ' + e.message;
  }
});

uploadBtn.addEventListener('click', async () => {
  const file = pdfInput.files?.[0];
  if (!file) {
    uploadStatus.textContent = 'Please choose a PDF file to upload.';
    return;
  }
  const form = new FormData();
  form.append('file', file);
  uploadStatus.textContent = 'Uploading...';
  try {
    const res = await fetch('/upload_pdf', {
      method: 'POST',
      body: form
    });
    if (!res.ok) throw new Error('Upload failed');
    const data = await res.json();
    uploadStatus.textContent = `Uploaded and ingested: ${data.file_id}`;
  } catch (e) {
    uploadStatus.textContent = 'Error: ' + e.message;
  }
});

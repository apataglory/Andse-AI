document.addEventListener("DOMContentLoaded", () => {
    const attachBtn = document.getElementById('attach-btn'); // Make sure to add this ID in HTML!
    const inputZone = document.querySelector('.max-w-4xl.mx-auto.bg-gray-850'); // The text box container
    
    // 1. Create a hidden file input
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.style.display = 'none';
    fileInput.accept = 'image/*,.pdf,.doc,.docx,.txt,.mp4,.csv';
    document.body.appendChild(fileInput);

    // 2. Create a UI container for the "Preview Chip" (shows what file is staged)
    const stagingArea = document.createElement('div');
    stagingArea.className = 'w-full px-4 pt-2 hidden flex items-center gap-2 overflow-x-auto';
    inputZone.parentElement.insertBefore(stagingArea, inputZone);

    // Global variable to hold staged file data so chat.js can send it
    window.stagedFile = null;

    attachBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // UI Feedback: Show uploading state
        attachBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        const formData = new FormData();
        formData.append('file', file);

        try {
            // 1. Send file to the secure file_handler.py backend
            const response = await fetch('/chat/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // 2. Store the file info globally so chat.js can grab it
                window.stagedFile = {
                    filepath: data.filepath,
                    filename: data.filename,
                    type: data.type,
                    ext: file.name.split('.').pop().toLowerCase()
                };

                // 3. Render the Preview Chip
                renderFileChip(file.name, data.type);
            } else {
                alert("Upload failed: " + data.error);
            }
        } catch (error) {
            console.error("Upload error:", error);
        } finally {
            // Reset button
            attachBtn.innerHTML = '<i class="fa-solid fa-paperclip text-lg"></i>';
            fileInput.value = ''; // Clear input
        }
    });

    function renderFileChip(filename, type) {
        let icon = 'fa-file';
        if (type === 'images') icon = 'fa-image text-blue-400';
        if (type === 'documents') icon = 'fa-file-pdf text-red-400';
        if (type === 'videos') icon = 'fa-video text-purple-400';

        stagingArea.innerHTML = `
            <div class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 flex items-center gap-2 shadow-md animate-fade-in-up">
                <i class="fa-solid ${icon}"></i>
                <span class="text-xs text-gray-200 max-w-[150px] truncate">${filename}</span>
                <button id="remove-file-btn" class="text-gray-500 hover:text-red-400 ml-2">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
        `;
        stagingArea.classList.remove('hidden');

        // Handle removing the file
        document.getElementById('remove-file-btn').addEventListener('click', () => {
            window.stagedFile = null;
            stagingArea.innerHTML = '';
            stagingArea.classList.add('hidden');
        });
    }
});
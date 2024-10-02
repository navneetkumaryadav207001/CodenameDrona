// Select DOM elements
const newNoteBtn = document.getElementById('new-note');
const saveNoteBtn = document.getElementById('save-note');
const notepad = document.getElementById('notepad');
const savedNotesContainer = document.getElementById('savedNotes');

// Load saved notes when the page loads
document.addEventListener('DOMContentLoaded', loadSavedNotes);

// Event listener for creating a new note
newNoteBtn.addEventListener('click', () => {
  notepad.value = '';  // Clear the textarea for a new note
});

// Event listener for saving the note
saveNoteBtn.addEventListener('click', () => {
  const noteText = notepad.value.trim();
  if (noteText) {
    saveNoteToLocalStorage(noteText);
    notepad.value = '';  // Clear the notepad after saving
    loadSavedNotes();  // Reload the saved notes list
  }
});

// Save the note to localStorage
function saveNoteToLocalStorage(note) {
  let notes = getNotesFromLocalStorage();  // Fetch existing notes
  notes.push(note);  // Add the new note
  localStorage.setItem('notes', JSON.stringify(notes));  // Save notes to localStorage
}

// Load saved notes from localStorage and display them
function loadSavedNotes() {
  const notes = getNotesFromLocalStorage();
  savedNotesContainer.innerHTML = '';  // Clear the current list

  notes.forEach((note, index) => {
    const noteDiv = document.createElement('div');
    noteDiv.classList.add('note-item');
    noteDiv.innerHTML = `
      <p>${note}</p>
      <button onclick="deleteNote(${index})">🗑️Delete</button>
    `;
    savedNotesContainer.appendChild(noteDiv);
  });
}

// Get notes from localStorage
function getNotesFromLocalStorage() {
  const notes = localStorage.getItem('notes');
  return notes ? JSON.parse(notes) : [];
}

// Delete a note by index and update localStorage
function deleteNote(index) {
  let notes = getNotesFromLocalStorage();
  notes.splice(index, 1);  // Remove the note at the given index
  localStorage.setItem('notes', JSON.stringify(notes));  // Save the updated notes
  loadSavedNotes();  // Reload the notes list
}

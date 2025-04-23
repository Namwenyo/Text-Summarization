const textarea = document.getElementById("text-input");
const initialState = document.getElementById("initial-state");
const fileUpload = document.getElementById("file-upload");
const uploadLabel = document.getElementById("upload-label");
const uploadBox = document.getElementById("upload-box");
const pasteBtn = document.getElementById("paste-btn");
const inputWordCount = document.getElementById("input-word-count");
const summarizeBtn = document.getElementById("summarize-btn");
const formatButtons = document.querySelectorAll(".format-option");
const summaryOutput = document.getElementById("summary-output");
const wordCount = document.getElementById("word-count");
const copyOutput = document.getElementById("copy-output");

let selectedFormat = "paragraph";

function showTextOnly() {
  initialState.style.display = "none";
  textarea.style.display = "block";
  textarea.focus();
}

function updateInputWordCount() {
  const words = textarea.value.trim().split(/\s+/).filter(w => w.length > 0);
  inputWordCount.textContent = `Word count: ${words.length}`;
}

textarea.addEventListener("input", () => {
  if (textarea.value.trim()) {
    showTextOnly();
  } else {
    initialState.style.display = "flex";
  }
  updateInputWordCount();
});

uploadLabel.addEventListener("click", () => fileUpload.click());

fileUpload.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  fetch("/upload", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
      } else {
        textarea.value = data.text;
        showTextOnly();
        updateInputWordCount();
      }
    })
    .catch(() => alert("Failed to upload file."));
});

pasteBtn.addEventListener("click", async () => {
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      textarea.value = text;
      showTextOnly();
      updateInputWordCount();
    } else {
      alert("Clipboard is empty!");
    }
  } catch (err) {
    alert("Clipboard access not allowed. Please allow permissions.");
  }
});

formatButtons.forEach(button => {
  button.addEventListener("click", () => {
    formatButtons.forEach(btn => btn.classList.remove("selected"));
    button.classList.add("selected");
    selectedFormat = button.dataset.format;
  });
});

summarizeBtn.addEventListener("click", async () => {
    const text = textarea.value.trim();
    if (!text) return alert("Please enter or paste some text first.");
  
    try {
      const res = await fetch("/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, format: selectedFormat })
      });
  
      const data = await res.json();
  
      if (!res.ok) {
        alert(data.error || "Something went wrong.");
        return;
      }
  
      summaryOutput.innerHTML = formatSummary(data.summary, selectedFormat);
      wordCount.textContent = `word count: ${data.summary.split(/\s+/).length}`;
    } catch (err) {
      alert("Something went wrong with summarization.");
      console.error(err);
    }
  });  

function formatSummary(summary, format) {
  const lines = summary.split("\n").filter(line => line.trim());
  if (format === "bullets") {
    return lines.map(line => `• ${line}`).join("\n");
  } else if (format === "numbered") {
    return lines.map((line, idx) => `${idx + 1}. ${line}`).join("\n");
  }
  return summary;
}

copyOutput.addEventListener("click", () => {
  navigator.clipboard.writeText(summaryOutput.textContent)
    .then(() => alert("Copied to clipboard!"))
    .catch(() => alert("Failed to copy"));
});

// Drag-and-drop support
uploadBox.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadBox.classList.add("dragover");
});

uploadBox.addEventListener("dragleave", () => {
  uploadBox.classList.remove("dragover");
});

uploadBox.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadBox.classList.remove("dragover");

  const file = e.dataTransfer.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  fetch("/upload", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
      } else {
        textarea.value = data.text;
        showTextOnly();
        updateInputWordCount();
      }
    })
    .catch(() => alert("Failed to upload file."));
});

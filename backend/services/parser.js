const pdfParse = require('pdf-parse');

async function extractTextFromBuffer(buffer, mimetype) {
  if (!buffer || buffer.length === 0) {
    throw new Error('Empty file received.');
  }

  if (mimetype === 'application/pdf') {
    try {
      const data = await pdfParse(buffer);
      if (!data.text || data.text.trim().length === 0) {
        throw new Error('No readable text found in this PDF. It may be a scanned image.');
      }
      return { type: 'text', content: data.text };
    } catch (err) {
      throw new Error('Could not read PDF: ' + err.message);
    }
  }

  if (mimetype.startsWith('image/')) {
    const base64 = buffer.toString('base64');
    return { type: 'image', content: base64, mimetype };
  }

  throw new Error('Unsupported file type. Please upload a PDF or image file.');
}

module.exports = { extractTextFromBuffer };

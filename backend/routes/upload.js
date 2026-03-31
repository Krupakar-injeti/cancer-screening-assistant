const express = require('express');
const multer = require('multer');
const { extractTextFromBuffer } = require('../services/parser');

const router = express.Router();

const ALLOWED_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/jpg',
  'image/png',
  'image/webp'
];

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 20 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    if (ALLOWED_TYPES.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only PDF, JPG, PNG, and WEBP are allowed.'));
    }
  }
});

router.post('/', upload.single('report'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded.' });
    }

    const documentData = await extractTextFromBuffer(req.file.buffer, req.file.mimetype);

    res.json({
      success: true,
      documentData,
      fileName: req.file.originalname,
      fileSize: req.file.size,
      fileType: req.file.mimetype
    });
  } catch (err) {
    console.error('Upload error:', err.message);
    res.status(500).json({ error: err.message || 'Failed to process the file.' });
  }
});

module.exports = router;

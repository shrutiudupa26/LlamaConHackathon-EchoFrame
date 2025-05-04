import OpenAI from 'openai';
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import bodyParser from 'body-parser';
import multer from 'multer';

dotenv.config();

const app = express();
app.use(cors());
app.use(bodyParser.json());

// Configure multer for file uploads
const storage = multer.memoryStorage();
const upload = multer({ storage });

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: 'https://api.groq.com/openai/v1'
});

app.post('/api/summarize-file', upload.single('file'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded.' });
  }

  try {
    // Log the file buffer size for debugging
    console.log(`File uploaded with size: ${req.file.size} bytes`);

    // Ensure the file is passed as a buffer
    const pdfText = await pdfParse(req.file.buffer);  // Pass file buffer, not a file path

    if (!pdfText.text) {
      return res.status(400).json({ error: 'Unable to extract text from PDF.' });
    }

    // Proceed with summarization using the extracted text
    const completion = await openai.chat.completions.create({
      model: 'meta-llama/llama-4-maverick-17b-128e-instruct', // or another model
      messages: [
        { role: 'system', content: 'You are a helpful summarizer.' },
        { role: 'user', content: `Summarize this:\n\n${pdfText.text}` }
      ]
    });

    res.json({ summary: completion.choices[0].message.content });
  } catch (err) {
    console.error('Error during file processing:', err);
    res.status(500).json({ error: 'File summarization failed.' });
  }
});

// ✅ POST /api/ask
app.post('/api/ask', async (req, res) => {
  const { question } = req.body;
  try {
    const completion = await openai.chat.completions.create({
      model: 'meta-llama/llama-4-maverick-17b-128e-instruct', // or use llama3-8b or llama3-70b-8192
      messages: [
        { role: 'system', content: 'You are a helpful assistant.' },
        { role: 'user', content: question }
      ]
    });
    res.json({ answer: completion.choices[0].message.content });
  } catch (err) {
    console.error('Error during question answering:', err);
    res.status(500).json({ error: 'Question answering failed.' });
  }
});

app.listen(3001, () => console.log('Backend running at http://localhost:3001'));
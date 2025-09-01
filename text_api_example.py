// To run this code you need to install the following dependencies:
// npm install @google/genai mime
// npm install -D @types/node

import {
  GoogleGenAI,
} from '@google/genai';

async function main() {
  const ai = new GoogleGenAI({
    apiKey: process.env.GEMINI_API_KEY,
  });
  const config = {
    thinkingConfig: {
      thinkingBudget: -1,
    },
  };
  const model = 'gemini-2.5-flash';
  const contents = [
    {
      role: 'user',
      parts: [
        {
          text: `Create a comic book title`,
        },
      ],
    },
    {
      role: 'model',
      parts: [
        {
          text: `Okay, how about:

*   **The Quantum Vanguard**
*   **Aetheria: The Last Spellbinder**
*   **Neon Echoes**
*   **The Chrononaut's Creed**
*   **Crimson Tides**

Do any of those spark your interest, or would you like me to generate an image for one of them?
`,
        },
      ],
    },
    {
      role: 'user',
      parts: [
        {
          text: `INSERT_INPUT_HERE`,
        },
      ],
    },
  ];

  const response = await ai.models.generateContentStream({
    model,
    config,
    contents,
  });
  let fileIndex = 0;
  for await (const chunk of response) {
    console.log(chunk.text);
  }
}

main();

# ChapterLens — Chapter Readability Analyzer

ChapterLens is a free, local Streamlit app for authors. Paste a chapter to see a Flesch Reading Ease score, writing statistics, the five most difficult sentences, revision ideas, and an exact visual map of those sentences in the original text.

Readability scores are estimates based on language patterns. They are not definitive judgments of writing quality, voice, or literary merit.

## Project structure

```text
chapterlens/
├── app.py
├── requirements.txt
└── README.md
```

## Run locally on Windows (VS Code)

Open the project folder in VS Code, then open **Terminal → New Terminal** and run:

```powershell
cd D:\chapterlens
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run this once in the same terminal:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Streamlit will print a local URL, usually `http://localhost:8501`. Stop the app with `Ctrl+C`.

## What the analyzer does

- Calculates Flesch Reading Ease locally with `textstat`.
- Uses a built-in syllable estimator if `textstat` is unavailable or cannot score a passage.
- Ranks sentences using length, long-word frequency, average word length, and syllable density.
- Preserves sentence positions so highlights always map to the original chapter.
- Estimates reading time at 220 words per minute.

No text is sent to a paid API, and no account or API key is needed.

## Free deployment with Streamlit Community Cloud

1. Create a GitHub repository, for example `chapterlens`.
2. Upload `app.py`, `requirements.txt`, and `README.md` to the repository.
3. Visit [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
4. Choose **New app**, select your repository and branch, and set the main file to `app.py`.
5. Click **Deploy**. Streamlit Community Cloud installs the packages from `requirements.txt`.

The app is stateless and has no secrets, database, or paid services to configure.

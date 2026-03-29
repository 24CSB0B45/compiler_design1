# 🛠️ Self-Healing Agentic Compiler

> An intelligent compiler that **detects, fixes, and verifies code automatically** using AI-driven agents.

---

## 🚀 Overview

The **Self-Healing Agentic Compiler** is an advanced system designed to automatically identify software vulnerabilities and programming errors, apply safe fixes, and verify correctness — all with minimal human intervention.

It combines:

* 🧠 **LLM-based reasoning (Gemini API)**
* 🔍 **Static analysis (AST-based)**
* 🔁 **Agentic feedback loops**
* ✅ **Automated verification**

---

## 🎯 Objective

Build a compiler-like system that:

* Detects bugs and vulnerabilities in Python code
* Automatically generates safe fixes
* Verifies correctness after repair
* Reduces manual debugging effort and security risks

---

## 🧩 Key Features

### 🔍 Vulnerability Detection

* Detect unsafe patterns like:

  * `eval()` usage ⚠️
  * Injection vulnerabilities 💉
  * Unsafe API calls 🔓
* Uses **AST-based static analysis**

### 🛠️ Automated Code Repair

* LLM-driven transformations via Gemini
* Safe and constraint-based fixes
* Maintains semantic correctness

### 🔁 Agentic Loop

```
Compile → Detect → Fix → Test → Verify → Repeat
```

### ✅ Verification Engine

* Regression testing
* Runtime assertions
* Ensures no new bugs are introduced

---

## 📂 Project Structure

```
.
├── agent.py
├── app.py
├── transformation.py
├── verification_engine.py
├── vulnerability_detector.py
└── README.md
```

### 📄 File Responsibilities

* 🤖 **agent.py**
  Core LLM-powered agent that:
  
  * Orchestrates all modules
  * Detects issues
  * Decides fixes
  * Drives the detect → fix → verify loop

* 🌐 **app.py**
  Flask application that:

  * Provides a web interface
  * Connects frontend with backend logic

* 🔧 **transformation.py**
  Applies safe code transformations based on agent decisions

* 🛡️ **verification_engine.py**
  Verifies correctness of modified code using:

  * Tests
  * Assertions
  * Validation logic

* 🔎 **vulnerability_detector.py**
  Detects vulnerabilities using static analysis techniques

---

## ⚙️ How to Use (Step-by-Step)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/self-healing-agentic-compiler.git
cd self-healing-agentic-compiler
```

---

### 2️⃣ Create a Virtual Environment

```bash
python3 -m venv venv
```

---

### 3️⃣ Activate the Virtual Environment

#### On macOS / Linux:

```bash
source venv/bin/activate
```

#### On Windows:

```bash
venv\Scripts\activate
```

---

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5️⃣ Set Gemini API Key 🔑

```bash
export GEMINI_API_KEY="your api key"
```

> ⚠️ Make sure you have a valid Gemini API key before running the project.

---

### 6️⃣ Run the Application 🚀

```bash
python app.py
```

---

### 7️⃣ Open in Browser 🌐

Go to:

```
http://127.0.0.1:5000
```

---

## 🧪 Example Workflow

### Input Code

```python
user_input = input()
eval(user_input)
```

### Detected Issue ⚠️

* Unsafe use of `eval()` → Code Injection Risk

### Fixed Code ✅

```python
import ast
user_input = input()
ast.literal_eval(user_input)
```

---

## 🧠 Technologies Used

* 🐍 Python
* 🔎 `ast` module
* 🤖 Gemini API (LLM)
* 🌐 Flask (Web UI)

---

## ⚠️ Challenges

* LLM hallucinations 🤯
* Ensuring semantic correctness
* Avoiding unsafe fixes
* Balancing precision vs recall

---

## 📈 Evaluation Metrics

* 🎯 Detection Accuracy
* 🛠️ Fix Precision
* ❌ False Positives / Negatives
* ⚡ Performance Overhead

---

## 🔮 Future Scope

* Multi-language support 🌍
* IDE integration 💻
* Real-time code healing ✨
* CI/CD integration 🔄

---

## 👨‍💻 Author

**Miryala Avas**
B.Tech - Computer Science and Engineering

---

## ⭐ Contribute

* Fork the repo 🍴
* Create a branch 🌿
* Submit a PR 🚀

---

## 📜 License

For academic and research purposes.

---

## 💡 Final Thought

> "What if compilers didn’t just detect errors… but fixed them automatically?"

✨ *Build smarter. Fix automatically. Ship securely.* ✨

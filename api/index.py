import os
import requests
import gradio as gr
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fpdf import FPDF

app = FastAPI()

HF_TOKEN = os.environ.get("OPENAI_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def clean_topic(topic):
    topic = topic.lower()
    if "write a blog on" in topic:
        topic = topic.replace("write a blog on", "").strip()
    elif "write a blog about" in topic:
        topic = topic.replace("write a blog about", "").strip()
    return topic.capitalize()

def generate_blog(topic):
    topic = clean_topic(topic)
    prompt = f"""### Instruction:
Write a complete, friendly, and engaging blog post about "{topic}".
Structure the blog with: a title, intro, subheadings, conclusion.

### Response:
"""
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 700,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        generated_text = response.json()[0]['generated_text']
        blog = generated_text.split("### Response:")[-1].strip()
        return blog, blog
    except Exception as e:
        return f"❌ Failed to generate blog: {str(e)}", f"❌ Failed to generate blog: {str(e)}"

def download_txt(text):
    path = "/tmp/blog.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def download_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    path = "/tmp/blog.pdf"
    pdf.output(path)
    return path

with gr.Blocks() as demo:
    gr.Markdown("## 📝 AI Blog Writer with Copy & Download Options")

    topic = gr.Textbox(label="Enter Blog Topic", placeholder="e.g. Clean energy")
    generate_btn = gr.Button("✍️ Generate Blog")

    with gr.Row():
        output_box = gr.Textbox(label="Generated Blog", lines=20)
        preview = gr.Markdown()

    with gr.Row():
        copy_btn = gr.Button("📋 Copy")
        txt_btn = gr.Button("⬇️ Download .txt")
        pdf_btn = gr.Button("🧾 Download .pdf")

    txt_file = gr.File(visible=False)
    pdf_file = gr.File(visible=False)

    generate_btn.click(fn=generate_blog, inputs=topic, outputs=[output_box, preview])
    txt_btn.click(fn=download_txt, inputs=output_box, outputs=txt_file)
    pdf_btn.click(fn=download_pdf, inputs=output_box, outputs=pdf_file)

    txt_file.render()
    pdf_file.render()

    copy_btn.click(None, None, None, _js="""
        () => {
            const textarea = document.querySelector('textarea');
            textarea.select();
            document.execCommand('copy');
            alert('Copied to clipboard!');
        }
    """)

# Mount as FastAPI route
app = gr.mount_gradio_app(app, demo, path="/")

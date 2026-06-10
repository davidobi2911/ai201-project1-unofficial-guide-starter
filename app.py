"""Milestone 5 (interface) — Gradio chat UI for the Unofficial UW Guide.

A chat box backed by the grounded-generation pipeline (query.answer), with a side
panel showing the chunks that were retrieved for each question and their distances.

Run:
    python app.py
Then open the printed local URL (default http://127.0.0.1:7860).
"""

from __future__ import annotations

import gradio as gr

from index import build_index
from query import answer

INTRO = (
    "# The Unofficial UW Guide\n"
    "Ask about UW dorms, dining, professors, registration, academic support, or "
    "F-1/visa status. Answers are grounded **only** in the guide documents — if the "
    "answer isn't in them, the guide will say so."
)
SOURCES_PLACEHOLDER = "### Retrieved sources\n_Ask a question to see the chunks used._"


def _snippet(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _sources_markdown(result: dict) -> str:
    lines = ["### Sources used"]
    if result["sources"]:
        for s in result["sources"]:
            label = s["source_label"] or s["source_file"]
            lines.append(f"- **{label}**  \n  `{s['source_file']}`")
    else:
        lines.append("_(none relevant)_")

    lines.append("\n### Retrieved chunks (top-5)")
    for r in result["retrieved"]:
        lines.append(
            f"**[{r['rank']}]** `{r['source_file']}` · dist {r['distance']:.2f}\n\n"
            f"> {_snippet(r['text'])}"
        )
    return "\n\n".join(lines)


def respond(message: str, history: list[dict]):
    message = (message or "").strip()
    if not message:
        return history, "", SOURCES_PLACEHOLDER

    result = answer(message)
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": result["answer"]},
    ]
    return history, "", _sources_markdown(result)


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="The Unofficial UW Guide") as demo:
        gr.Markdown(INTRO)
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(height=460, label="Chat")
                msg = gr.Textbox(
                    placeholder="Ask a question about UW…",
                    show_label=False,
                    submit_btn=True,
                )
                clear = gr.Button("Clear")
            with gr.Column(scale=2):
                sources = gr.Markdown(SOURCES_PLACEHOLDER)

        msg.submit(respond, [msg, chatbot], [chatbot, msg, sources])
        clear.click(lambda: ([], "", SOURCES_PLACEHOLDER), None, [chatbot, msg, sources])
    return demo


if __name__ == "__main__":
    build_index()  # build/reuse the vector store before serving
    build_ui().launch()

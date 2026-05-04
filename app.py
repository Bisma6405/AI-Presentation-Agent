import streamlit as st
import json
import os
from io import BytesIO
from pathlib import Path
from groq_client import GroqClient
from slide_generator import SlideGenerator
from image_fetcher import ImageFetcher

# ─────────────────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎯 AI Presentation Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .slide-preview {
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 30px;
        min-height: 450px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.08);
        font-family: 'Segoe UI', sans-serif;
    }
    .slide-title {
        font-size: 28px;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 16px;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 10px;
    }
    .slide-bullet {
        margin: 10px 0;
        padding-left: 24px;
        position: relative;
        color: #334155;
        font-size: 17px;
        line-height: 1.5;
    }
    .slide-bullet::before {
        content: "•";
        color: #3b82f6;
        font-weight: bold;
        font-size: 22px;
        position: absolute;
        left: 4px;
        top: -2px;
    }
    .control-card {
        background: #f8fafc;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 16px;
        border: 1px solid #e2e8f0;
    }
    .stButton > button {
        background-color: #3b82f6;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        padding: 8px 16px;
    }
    .stButton > button:hover {
        background-color: #2563eb;
    }
    .progress-text {
        color: #64748b;
        font-size: 14px;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Check API Key
# ─────────────────────────────────────────────────────────────
if not os.getenv("GROQ_API_KEY"):
    st.error("❌ GROQ_API_KEY not found in .env file!")
    st.stop()

# ─────────────────────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────────────────────
if "initialized" not in st.session_state:
    st.session_state.update({
        "title": "",
        "outline": [],
        "slides": [],
        "current_idx": 0,
        "groq": GroqClient(),
        "image_fetcher": ImageFetcher(),
        "generator": SlideGenerator(),
        "initialized": True
    })


# ─────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────
def parse_json_response(raw_text: str) -> dict | list:
    """Safely parse JSON from Groq, stripping markdown if present"""
    try:
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON parsing error: {e}")
        with st.expander("View raw response"):
            st.text(raw_text[:1000])
        raise


def render_preview(slide: dict) -> str:
    """Generate HTML preview for a slide"""
    if slide["type"] == "title":
        return f"""
        <div class="slide-preview" style="text-align: center; display: flex; flex-direction: column; justify-content: center;">
            <div class="slide-title" style="font-size: 38px; border: none; color: #0f172a;">
                {slide.get('heading', 'Presentation Title')}
            </div>
            <div style="font-size: 20px; color: #64748b; margin-top: 12px;">
                {slide.get('subtitle', '')}
            </div>
        </div>"""

    bullets = "".join(f'<div class="slide-bullet">{p}</div>' for p in slide.get("bullet_points", []))
    img_badge = f'<div style="margin-top:20px; padding:8px 12px; background:#f1f5f9; border-radius:6px; display:inline-block; font-size:13px; color:#64748b;">🖼️ Image: {slide.get("image_query", "N/A")}</div>' if slide.get("image_path") else ""

    return f"""
    <div class="slide-preview">
        <div class="slide-title">{slide.get('heading', 'Slide Title')}</div>
        <div>{bullets}</div>
        {img_badge}
    </div>"""


def build_and_download_pptx() -> BytesIO:
    """Build PPTX from session slides and return BytesIO"""
    st.session_state.generator.reset()
    for s in st.session_state.slides:
        if s["type"] == "title":
            st.session_state.generator.add_title_slide(s["heading"], s.get("subtitle", ""))
        else:
            st.session_state.generator.add_content_slide(
                heading=s["heading"],
                bullet_points=s.get("bullet_points", []),
                image_path=s.get("image_path")
            )
    return st.session_state.generator.save_to_bytes()


# ─────────────────────────────────────────────────────────────
# Main UI Layout
# ─────────────────────────────────────────────────────────────
st.title("🎯 AI Presentation Agent")
st.markdown("Create professional slides step-by-step with AI")
st.divider()

col_preview, col_controls = st.columns([1, 1])

# ─────────────────────────────────────────────────────────────
# LEFT COLUMN: Slide Preview
# ─────────────────────────────────────────────────────────────
with col_preview:
    st.subheader("📊 Slide Preview")

    if not st.session_state.slides:
        st.info("👈 Start by entering a title and generating an outline on the right.")
    else:
        # Navigation
        slide_selector = st.selectbox(
            "Select Slide",
            options=range(len(st.session_state.slides)),
            format_func=lambda x: f"Slide {x + 1} • {st.session_state.slides[x]['heading'][:30]}",
            key="preview_selector"
        )

        # Render Preview
        st.markdown(render_preview(st.session_state.slides[slide_selector]), unsafe_allow_html=True)

        # Quick overview
        if len(st.session_state.slides) > 1:
            st.caption(f"Slide {slide_selector + 1} of {len(st.session_state.slides)}")

# ─────────────────────────────────────────────────────────────
# RIGHT COLUMN: Controls
# ─────────────────────────────────────────────────────────────
with col_controls:
    st.subheader("🎛️ Controls")

    # 1️⃣ Title
    with st.expander("1️⃣ Presentation Title", expanded=not bool(st.session_state.title)):
        title_input = st.text_input(
            "Enter Topic / Title",
            value=st.session_state.title,
            placeholder="e.g., The Future of Artificial Intelligence"
        )
        if st.button("✅ Set Title", use_container_width=True, disabled=not title_input.strip()):
            st.session_state.title = title_input.strip()
            st.success(f"Title locked: `{st.session_state.title}`")
            st.rerun()

    # 2️⃣ Generate Outline
    with st.expander("2️⃣ Generate Outline", expanded=bool(st.session_state.title and not st.session_state.outline)):
        if st.button("🤖 AI Generate Outline", use_container_width=True, disabled=not st.session_state.title):
            with st.spinner("🧠 Analyzing topic & structuring slides..."):
                try:
                    raw = st.session_state.groq.generate_outline(st.session_state.title)
                    st.session_state.outline = parse_json_response(raw)
                    st.session_state.slides = []
                    st.session_state.current_idx = 0
                    st.session_state.generator.reset()
                    st.success(f"✅ Outline ready! ({len(st.session_state.outline)} slides)")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Outline generation failed: {e}")
                    st.stop()

    # 3️⃣ Create Slides One-by-One
    if st.session_state.outline:
        remaining = len(st.session_state.outline) - st.session_state.current_idx
        st.markdown(
            f'<div class="progress-text">Progress: {st.session_state.current_idx}/{len(st.session_state.outline)} slides</div>',
            unsafe_allow_html=True)
        st.progress(st.session_state.current_idx / len(st.session_state.outline))

        with st.expander("3️⃣ Create Next Slide", expanded=bool(remaining > 0)):
            if remaining > 0:
                next_slide = st.session_state.outline[st.session_state.current_idx]
                st.info(f"**Up Next:** Slide {st.session_state.current_idx + 1} → `{next_slide['heading']}`")

                if st.button("▶️ Create Next Slide", type="primary", use_container_width=True):
                    with st.spinner("🎨 Generating content & fetching visuals..."):
                        try:
                            # AI Content
                            content_raw = st.session_state.groq.generate_slide_content(st.session_state.title, next_slide)
                            content = parse_json_response(content_raw)

                            # Image
                            img_path = None
                            if content.get("image_search_query"):
                                st.caption("📷 Fetching relevant image...")
                                img_path = st.session_state.image_fetcher.fetch_image(content["image_search_query"])

                            # Build Slide Dict
                            new_slide = {
                                "type": next_slide.get("type", "content"),
                                "heading": content.get("heading", next_slide["heading"]),
                                "bullet_points": content.get("bullet_points", []),
                                "image_path": img_path,
                                "image_query": content.get("image_search_query", ""),
                                "subtitle": st.session_state.title if next_slide.get("type") == "title" else ""
                            }

                            st.session_state.slides.append(new_slide)
                            st.session_state.current_idx += 1
                            st.success("✅ Slide added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Slide creation failed: {e}")
                            st.stop()
            else:
                st.success("🎉 All slides generated!")

    # 4️⃣ Edit Content
    if st.session_state.slides:
        with st.expander("4️⃣ Edit Slide Content", expanded=False):
            edit_idx = st.selectbox(
                "Select Slide to Edit",
                options=range(len(st.session_state.slides)),
                format_func=lambda x: f"Slide {x + 1}",
                key="edit_selector"
            )

            target = st.session_state.slides[edit_idx]
            new_head = st.text_input("Heading", value=target["heading"], key=f"h_{edit_idx}")

            st.markdown("**Bullet Points**")
            new_bullets = []
            for i, pt in enumerate(target.get("bullet_points", [])):
                nb = st.text_input(f"Point {i + 1}", value=pt, key=f"b_{edit_idx}_{i}")
                if nb.strip():
                    new_bullets.append(nb.strip())

            if st.button("➕ Add Empty Point", use_container_width=True):
                new_bullets.append("New point")
                st.rerun()

            if st.button("💾 Save Edits", type="secondary", use_container_width=True):
                st.session_state.slides[edit_idx]["heading"] = new_head
                st.session_state.slides[edit_idx]["bullet_points"] = new_bullets
                st.success("✅ Changes saved!")
                st.rerun()

    # 5️⃣ Download
    if st.session_state.slides:
        with st.expander("5️⃣ Export & Download", expanded=False):
            st.markdown("Your presentation is ready. Click below to download the `.pptx` file.")
            if st.button("📥 Download PowerPoint", type="primary", use_container_width=True):
                try:
                    pptx_bytes = build_and_download_pptx()
                    st.download_button(
                        label="⬇️ Click to Save",
                        data=pptx_bytes,
                        file_name=f"{st.session_state.title.replace(' ', '_')[:50]}.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"❌ Export failed: {e}")

    # Reset
    st.divider()
    if st.button("🔄 Start New Presentation", use_container_width=True):
        st.session_state.update({
            "title": "",
            "outline": [],
            "slides": [],
            "current_idx": 0,
            "generator": SlideGenerator()
        })
        st.rerun()

# Footer
st.divider()
st.caption("Powered by Groq AI • Built with Streamlit • Images via Unsplash/Local Fallback")
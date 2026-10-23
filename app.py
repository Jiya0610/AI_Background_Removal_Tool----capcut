
try:
    original = open_uploaded_image(uploaded)
except ImageValidationError as exc:
    st.error(str(exc))
    st.stop()

digest = hashlib.sha256(uploaded.getvalue()).hexdigest()
if st.session_state.get("image_digest") != digest:
    st.session_state.image_digest = digest
    st.session_state.pop("result_rgba", None)
    st.session_state.pop("foreground_mask", None)
    st.session_state.pop("processed_digest", None)

left, right = st.columns([1, 1.25], gap="large")
with left:
    st.image(original, caption=f"Original · {original.width:,} × {original.height:,} px", use_container_width=True)
    st.caption(f"{uploaded.name} · {len(uploaded.getvalue()) / (1024 * 1024):.1f} MB")
    run = st.button("Remove background", type="primary", use_container_width=True, key="remove_background")
    if run:
        try:
            with st.spinner("Finding the subject and refining its edges…"):
                started = time.perf_counter()
                mask = generate_foreground_mask(original, get_model_session())
                elapsed = time.perf_counter() - started
            st.session_state.foreground_mask = mask
            st.session_state.processed_digest = digest
            st.session_state.processing_seconds = elapsed
        except ImportError:
            st.error("The AI dependencies aren't installed. Run `pip install -r requirements.txt`, then restart the app.")
        except RemovalError as exc:
            st.error(str(exc))
        except Exception as exc:  # Keep model/runtime failures inside the UI.
            st.error(f"The model couldn't process this image. Check your connection for the first model download, then try again. Details: {exc}")

with right:
    st.markdown('<div class="eyebrow">Step 02 · Preview & customize</div>', unsafe_allow_html=True)
    mask = st.session_state.get("foreground_mask") if st.session_state.get("processed_digest") == digest else None
    if mask is None:
        st.markdown("### Your result will appear here")
        st.markdown("Once you remove the background, your cutout and editing controls will appear here. You can refine the edges, try a new background, and export your finished image.")
    else:
        st.success(f"Background removed in {st.session_state.processing_seconds:.1f} seconds")
        softness = st.slider("Edge softness", 0.0, 2.5, 0.7, 0.1, help="Smooths jagged mask boundaries. Higher values soften fine details more.", key="edge_softness")
        rgba = apply_foreground_mask(original, mask, softness)
        with st.expander("Inspect AI mask"):
            st.caption("White pixels are retained as the subject; black pixels are removed as background.")
            st.image(mask, caption="Foreground mask", use_container_width=True)

        st.markdown("#### Choose a background")
        mode = st.radio("Background", ["Transparent", "Solid color", "Gradient", "Image"], horizontal=True, label_visibility="collapsed", key="background_mode")
        composed = rgba
        if mode == "Solid color":
            preset = st.selectbox("Color preset", ["Soft white", "Ink black", "Warm gray", "Custom"], key="color_preset")
            preset_colors = {"Soft white": "#F5F7F3", "Ink black": "#17221F", "Warm gray": "#D8D0C4"}
            color = st.color_picker("Background color", "#F5F7F3", key="background_color") if preset == "Custom" else preset_colors[preset]
            composed = composite_background(rgba, color=color)
        elif mode == "Gradient":
            g1, g2, g3 = st.columns(3)
            start = g1.color_picker("Gradient start", "#B9F36B", key="gradient_start")
            end = g2.color_picker("Gradient end", "#D9F3FF", key="gradient_end")
            angle = g3.slider("Angle", 0, 180, 35, key="gradient_angle")
            background = gradient_background(rgba.size, start, end, angle)
            composed = composite_background(rgba, background=background)
        elif mode == "Image":
            bg_upload = st.file_uploader("Choose a background image", type=["jpg", "jpeg", "png"], key="background_upload")
            if bg_upload is not None:
                try:
                    bg = open_uploaded_image(bg_upload, allow_large=False)
                    composed = composite_background(rgba, background=bg)
                except ImageValidationError as exc:
                    st.error(f"Background image: {exc}")
            else:
                st.caption("Upload a JPG or PNG. It will be resized to fit the subject image.")

        if mode == "Transparent":
            preview_background = checkerboard(rgba.size)
            comparison_after = composite_background(rgba, background=preview_background)
            jpeg_output = composite_background(rgba, color="#FFFFFF")
            png_output = rgba
        else:
            comparison_after = composed
            jpeg_output = composed
            png_output = composed
        st.markdown("#### Drag to compare")
        comparison_slider(original, comparison_after)
        transparent_data = png_bytes(rgba)
        dl1, dl2, dl3 = st.columns(3)
        dl1.download_button("Transparent PNG", transparent_data, file_name="background-removed.png", mime="image/png", use_container_width=True)
        dl2.download_button("Final PNG", png_bytes(png_output), file_name="background-customized.png", mime="image/png", use_container_width=True)
        dl3.download_button("Final JPEG", jpeg_bytes(jpeg_output), file_name="background-customized.jpg", mime="image/jpeg", use_container_width=True)

st.divider()
with st.expander("How it works and image limits"):
    st.markdown(
        """
        Images are checked for format, size, readability, and pixel dimensions before processing. OpenCV scales oversized images for model inference while preserving the aspect ratio; the resulting mask is then mapped back onto the original image. The lightweight U²-NetP model runs through `rembg`. On first use, it may need to download model weights, so an internet connection is required. The app doesn't write uploaded images or results to disk.

        **Limits:** JPG/PNG only · 20 MB maximum upload · 12,000 px per side · 40 million pixels maximum. Inference is capped at a 2,000 px longest side to limit memory use.
        """
    )

if st.button("Start over / upload another image", key="reset_app"):
    st.session_state.uploader_key = uploader_key + 1
    for key in ("image_digest", "result_rgba", "foreground_mask", "processed_digest", "processing_seconds", "background_upload"):
        st.session_state.pop(key, None)
    st.rerun()

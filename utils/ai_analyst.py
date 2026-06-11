import streamlit as st
import os
import anthropic

def render_analyst_box(module_id: str, module_name: str, context: str, extra_instruction: str = ""):
    """Renders a beautiful UI box in Streamlit for AI analyst interaction."""
    st.markdown("---")
    st.markdown(f"### 🤖 AI Agent Phân tích — {module_name}")
    
    # Check for Anthropic API key in environment or Streamlit secrets
    api_key = os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
    
    # Input for additional user questions
    question = st.text_input(
        f"Đặt câu hỏi cho AI Analyst về {module_name}:",
        placeholder="Ví dụ: Kịch bản phát triển kinh tế số 2030 có khả thi không? Tại sao?",
        key=f"q_{module_id}"
    )
    
    if st.button("Phân tích dữ liệu ⚡", key=f"btn_{module_id}", type="primary"):
        if not api_key:
            st.warning("⚠️ Chưa cấu hình ANTHROPIC_API_KEY. Dưới đây là phân tích mẫu từ AI Agent:")
            st.markdown(f"""
            **[Phân tích mẫu cho {module_name}]**
            
            Dựa trên dữ liệu và tham số mô phỏng hiện tại:
            - **Hiệu quả TFP**: Có xu hướng cải thiện, chứng tỏ chất lượng tăng trưởng được thúc đẩy bởi yếu tố công nghệ và số hóa.
            - **Đóng góp của Số hóa & AI**: Thể hiện đóng góp đáng kể. Khi tăng đầu tư và quy mô DN số (AI) cùng tỷ lệ lao động H, tốc độ tăng trưởng GDP tăng rõ rệt so với mô hình truyền thống chỉ dựa vào vốn K và lao động L thông thường.
            - **Tính khả thi của Kịch bản 2030**: Mức đóng góp của kinh tế số đạt mục tiêu 30% GDP đòi hỏi tốc độ tăng trưởng vốn số hóa liên tục và đào tạo nguồn nhân lực chất lượng cao rất lớn, phù hợp định hướng tại Nghị quyết 52-NQ/TW.
            
            *Vui lòng cung cấp `ANTHROPIC_API_KEY` trong biến môi trường hoặc Streamlit secrets để nhận phân tích thời gian thực từ Claude.*
            """)
        else:
            with st.spinner("AI Agent đang phân tích dữ liệu vĩ mô và mô hình tối ưu..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    prompt = f"""Bạn là chuyên gia kinh tế vĩ mô và chính sách công nghệ số tại Việt Nam.
Hãy phân tích kết quả của mô hình '{module_name}' dựa trên ngữ cảnh dữ liệu dưới đây.

Ngữ cảnh kết quả:
{context}

Yêu cầu phân tích thêm:
{extra_instruction}

Câu hỏi bổ sung từ người dùng:
{question if question else "Không có"}

Hãy đưa ra các nhận định sắc bén, sử dụng số liệu cụ thể từ ngữ cảnh, chỉ ra các phát hiện quan trọng và đề xuất khuyến nghị chính sách thực tế cho Việt Nam. Trả lời bằng tiếng Việt, định dạng Markdown đẹp, rõ ràng."""

                    message = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1500,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    st.markdown("#### 📝 Kết quả phân tích từ AI Agent")
                    st.markdown(message.content[0].text)
                except Exception as e:
                    st.error(f"Lỗi khi gọi API Anthropic: {e}")

import streamlit as st
st.sidebar.title("설정")
name = st.sidebar.text_input("이름")
st.title(f"환영합니다, {name}!")
col1, col2 = st.columns(2)
with col1:
    st.metric("오늘 방문자", "128")
with col2:
    st.metric("좋아요", "45")
tab1, tab2 = st.tabs(["소개", "활동 내역"])
with tab1:
    st.write("우리 동아리는...")
with tab2:
    st.write("3월: 파이썬 기초...")
with st.expander("채점 기준 보기"):
    st.write("1. 코드 실행 여부 (40점)")
    st.write("2. 인터페이스 완성도 (30점)")

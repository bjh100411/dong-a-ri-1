import streamlit as st
import random

st.title("🎯 숫자 맞추기 게임")

# 1) 게임 상태 초기화 (최초 1회만)
if "answer" not in st.session_state:
    st.session_state.answer = random.randint(1, 100)
    st.session_state.tries = 0

guess = st.number_input("1~100 사이 숫자", 1, 100, step=1)

if st.button("확인"):
    st.session_state.tries += 1
    if guess < st.session_state.answer:
        st.warning("⬆️ 더 큰 숫자예요!")
    elif guess > st.session_state.answer:
        st.warning("⬇️ 더 작은 숫자예요!")
    else:
        st.success(f"🎉 정답! {st.session_state.tries}번 만에 맞혔어요!")

st.caption(f"시도 횟수: {st.session_state.tries}")

if st.button("다시 시작"):
    del st.session_state.answer
    st.rerun()

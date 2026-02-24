import streamlit as st
import random
from plyer import notification

st.title("OTP Generator")
if st.button("Generate OTP"):
    otp = random.randint(100000, 999999)
    st.success(f"Your OTP is: {otp}")
    notification.notify(
        title="OTP Generated",
        message=f"Your OTP is: {otp}",
        timeout=5
    )



    st.set_page_config(
    page_title="NeoBank AI",
    page_icon="🏦",
    layout="wide"
)
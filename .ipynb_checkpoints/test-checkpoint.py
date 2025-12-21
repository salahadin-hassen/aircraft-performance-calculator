import streamlit as st

st.write("Hello World | by TheVoyager")

Equation = st.text_input("what's your favorite equation? ")
if bool(Equation) == True:
    st.write(f"your favorite equation is {Equation}, cool!")

clicked = st.button("Click me")
if clicked == True:
    st.write("goooooooood boy💀")
st.markdown("this is _markdown_")
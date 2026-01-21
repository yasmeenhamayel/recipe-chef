import streamlit as st
import pandas as pd
import ast
from load_data import load_recipes
from deep_translator import GoogleTranslator
import re

@st.cache_data
def get_data():
    df = load_recipes("recipes.csv")
    df['Cleaned_Ingredients'] = df['Cleaned_Ingredients'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df['Ingredients_str'] = df['Cleaned_Ingredients'].apply(lambda x: ' '.join(x).lower())
    return df

df = get_data()

def translate_input(text):
    if re.search(r'[\u0600-\u06FF]', text):
        try:
            return GoogleTranslator(source='auto', target='en').translate(text).lower()
        except:
            return text.lower()
    return text.lower()

if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.liked = ""
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm ChefBot. What would you like to cook today?"}]

st.title("🍳 ChefBot")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Enter ingredients (e.g., chicken, potato, onion...)."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    if st.session_state.step == 1:
        st.session_state.liked = translate_input(user_input)
        reply = "Great! Are there any ingredients you want to exclude or have allergies to? (Type 'no' if none)"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.step = 2
        st.rerun()

    elif st.session_state.step == 2:
        disliked_translated = translate_input(user_input)
        liked_words = st.session_state.liked.replace(",", " ").replace("and", " ").split()
        
        temp_df = df.copy()
        
        if "no" not in disliked_translated and "لا" not in user_input.lower():
            disliked_words = disliked_translated.replace(",", " ").replace("and", " ").split()
            for word in disliked_words:
                word = word.strip()
                if len(word) > 2:
                    temp_df = temp_df[~temp_df['Ingredients_str'].str.contains(word)]

        def calculate_score(row_text):
            score = 0
            for word in liked_words:
                word = word.strip()
                if len(word) > 2 and word in row_text:
                    score += 1
            return score

        temp_df['score'] = temp_df['Ingredients_str'].apply(calculate_score)
        results = temp_df[temp_df['score'] > 0].sort_values(by='score', ascending=False).head(3)

        if not results.empty:
            response = "Here are the top 3 recipes for you: \n\n"
            for i, (idx, recipe) in enumerate(results.iterrows()):
                response += f"### {i+1}. {recipe['Title']} 🍴\n"
                response += "**Ingredients:**\n"
                for ing in recipe['Cleaned_Ingredients']:
                    response += f"* {ing}\n"
                response += "\n---\n"
            response += "\n**Enjoy your meal! Want to try other ingredients? Just type them below 👇**"
        else:
            response = "Sorry, I couldn't find a match for those ingredients. Try different ones!"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.step = 1
        st.rerun()


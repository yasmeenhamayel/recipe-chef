import streamlit as st
import pandas as pd
import ast
from load_data import load_recipes
from deep_translator import GoogleTranslator

@st.cache_data
def get_data():
    df = load_recipes("recipes.csv")
    df['Cleaned_Ingredients'] = df['Cleaned_Ingredients'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df['Ingredients_str'] = df['Cleaned_Ingredients'].apply(lambda x: ' '.join(x).lower())
    return df

df = get_data()

def translate_input(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text).lower()
    except:
        return text.lower()

if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.liked = ""
    st.session_state.messages = [{"role": "assistant", "content": "أهلاً بك! شو حابب نطبخ اليوم؟"}]

st.title("🍳 ChifBot")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# التعديل هنا في النص التوضيحي (Placeholder)
if user_input := st.chat_input("اكتب المكونات مثل: دجاج، بطاطا..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    if st.session_state.step == 1:
        st.session_state.liked = translate_input(user_input)
        reply = "تمام، هل هناك أي مكونات لا تفضلها أو لديك حساسية منها؟ (إذا لا يوجد اكتب 'لا')"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.step = 2
        st.rerun()

    elif st.session_state.step == 2:
        disliked_translated = translate_input(user_input)
        liked_words = st.session_state.liked.replace("and", " ").split()
        
        temp_df = df.copy()
        
        if "no" not in disliked_translated and "لا" not in user_input:
            disliked_words = disliked_translated.replace("and", " ").split()
            for word in disliked_words:
                if len(word) > 2:
                    temp_df = temp_df[~temp_df['Ingredients_str'].str.contains(word)]

        def calculate_score(row_text):
            return sum(1 for word in liked_words if len(word) > 2 and word in row_text)

        temp_df['score'] = temp_df['Ingredients_str'].apply(calculate_score)
        results = temp_df[temp_df['score'] > 0].sort_values(by='score', ascending=False).head(3)

        if not results.empty:
            response = "إليك أفضل 3 وصفات تناسب طلبك: \n\n"
            for i, (idx, recipe) in enumerate(results.iterrows()):
                response += f"### {i+1}. {recipe['Title']} 🍴\n"
                response += "**المكونات (Ingredients):**\n"
                for ing in recipe['Cleaned_Ingredients']:
                    response += f"* {ing}\n"
                response += "\n---\n"
            
            response += "\n**أتمنى أن تنال إعجابك! إذا أردت البحث عن شيء آخر، اكتب المكونات هنا 👇**"
        else:
            response = "للأسف لم أجد وصفة مطابقة تماماً، جرب اقتراح مكونات أخرى!"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.step = 1
        st.rerun()

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.step = 1 

        st.rerun()



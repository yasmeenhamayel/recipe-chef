import streamlit as st
import pandas as pd
import ast
from load_data import load_recipes
from deep_translator import GoogleTranslator

# 1. تحميل البيانات
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

# 2. إعداد الحالة (Session State)
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.liked = ""
    st.session_state.messages = [{"role": "assistant", "content": "أهلاً ياسمين! شو حابة نطبخ اليوم؟"}]

st.title("🍳 شيف ياسمين الذكي")

# عرض سجل المحادثة (الفقاعات)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 3. استقبال المدخلات (الشات)
if user_input := st.chat_input("اكتبي هنا..."):
    # إضافة ردك للشاشة
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # الخطوة 1: المكونات المحبوبة
    if st.session_state.step == 1:
        st.session_state.liked = translate_input(user_input)
        reply = "تمام، وهل فيه أي مكونات بتكرهيها أو عندك حساسية منها؟ (إذا ما في اكتبي 'لا')"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.step = 2
        st.rerun()

    # الخطوة 2: البحث وعرض 3 وصفات مرتبة
    elif st.session_state.step == 2:
        disliked_translated = translate_input(user_input)
        liked_words = st.session_state.liked.replace("and", " ").split()
        
        temp_df = df.copy()
        
        # استبعاد المكونات المرفوضة
        if "no" not in disliked_translated and "لا" not in user_input:
            disliked_words = disliked_translated.replace("and", " ").split()
            for word in disliked_words:
                if len(word) > 2:
                    temp_df = temp_df[~temp_df['Ingredients_str'].str.contains(word)]

        # حساب نقاط التطابق
        def calculate_score(row_text):
            return sum(1 for word in liked_words if len(word) > 2 and word in row_text)

        temp_df['score'] = temp_df['Ingredients_str'].apply(calculate_score)
        results = temp_df[temp_df['score'] > 0].sort_values(by='score', ascending=False).head(3)

        # تجهيز الرد كرسالة واحدة طويلة تحتوي على 3 وصفات
        if not results.empty:
            response = "لقيت لك أفضل 3 وصفات بتناسب طلبك: \n\n"
            for i, (idx, recipe) in enumerate(results.iterrows()):
                response += f"### {i+1}. {recipe['Title']} 🍴\n"
                response += "**Ingredients (المكونات):**\n"
                # عرض المكونات تحت بعضها بنقاط
                for ing in recipe['Cleaned_Ingredients']:
                    response += f"* {ing}\n"
                response += "\n---\n" # خط فاصل
            
            response += "\n**شو رأيك؟ إذا حابة تبحثي عن شي ثاني، اكتبي المكونات هون 👇**"
        else:
            response = "للأسف ما لقيت وصفة مناسبة، جربي مكونات ثانية!"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.step = 1 # تصفير الخطوات للبحث الجديد
        st.rerun()
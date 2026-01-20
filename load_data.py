import pandas as pd

def load_recipes(path):
    df = pd.read_csv(path)
    
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    
    return df

df = load_recipes("recipes.csv")
def prepare_ingredients(df):
    df['Cleaned_Ingredients'] = df['Cleaned_Ingredients'].apply(ast.literal_eval)
    return df
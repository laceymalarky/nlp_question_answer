# Initialization
import spacy.cli
from transformers import pipeline
import pandas as pd
import numpy as np
import spacy
from spacy.tokens import DocBin
import streamlit as st
import en_core_web_md

# Streamlit app titles
st.title(':orange[DataSpeak] Q&A Chatbot💬')
# st.caption('The bot will return the top 5 possible answers to your question.')
st.divider()

# Load Data
df = pd.read_csv(
    'datasets/python_q_a_clean_score3_AandQwc150.csv')
df['title_question'] = df.title + '. ' + df.question

# Dowload spacy model
spacy.cli.download("en_core_web_md")

# Deserialize NLP docs
nlp = spacy.load("en_core_web_md", disable=['parser', 'ner'])
doc_bin = DocBin().from_disk(
    "datasets/python_qa_titlequest.spacy")
docs = list(doc_bin.get_docs(nlp.vocab))

# When a user submits a question, generate top 5 answers
prompt = st.chat_input("Ask a Question")
if prompt:
    st.write(f"**Question**: {prompt}")

    input_question = prompt

    # Generate top answer directly from user question
    generator = pipeline("text2text-generation",
                         model="lmalarky/flan-t5-base-finetuned-python_qa")
    answer_t5_main = generator(f"answer the question: {input_question}")

    st.write(f"**Answer:** {answer_t5_main[0]['generated_text']}")
    st.divider()

    # Calculate cosine similarity of input question, return top 5 questions in data
    st.write(f"Here are 5 alternate answers:")

    similarity = []
    input_text = nlp(input_question)

    for j in range(len(docs)):
        similarity.append(input_text.similarity(docs[j]))

    top5 = pd.DataFrame(np.array(similarity).T, columns=[
                        'similarity']).sort_values(by='similarity', ascending=False)
    top5 = top5.drop_duplicates()[:5]
    top5 = top5.join(df[['title', 'question', 'title_question']]
                     ).reset_index(drop=True)

    # Generate top 5 answers using top 5 title+quesitons from similarity analysis and % similarity

    def generate_5_answers(top5_input):
        output = []
        for context in top5_input:
            generator = pipeline("text2text-generation",
                                 model="lmalarky/flan-t5-base-finetuned-python_qa")
            answer_t5 = generator(f"answer the question: {context}")
            output.append(answer_t5[0]['generated_text'])
        return output

    answer_gen_top5 = generate_5_answers(top5['question'])
    answer_gen_top5 = pd.DataFrame(answer_gen_top5, columns=['generated_text'])
    top5_gen_answ = answer_gen_top5.join(top5[['similarity']])

    # Format output table
    top5_gen_answ['similarity'] = top5_gen_answ['similarity'].map(
        '{:.0%}'.format)
    top5_gen_answ.columns = ['Alternate Answer', '% Similarity']

    st.table(top5_gen_answ)

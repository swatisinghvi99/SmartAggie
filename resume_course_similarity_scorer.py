import pandas
import pandas as pd
from pyresparser import ResumeParser
from keybert import KeyBERT
import spacy

nlp = spacy.load("en_core_web_lg")


def parse_resume(resume_file:str) ->dict:
    data = ResumeParser(resume_file).get_extracted_data()
    return data


def keyword_parse(resume_data:dict, course_data:pandas.DataFrame, top_n:int =10) -> float:
    kw_model = KeyBERT(model='all-mpnet-base-v2')
    merged_course_data = ' '.join(course_data)
    keywords = kw_model.extract_keywords(merged_course_data,
                                         keyphrase_ngram_range=(1, 2),

                                         stop_words='english',

                                         highlight=False,

                                         top_n=top_n)

    keywords_list = list(dict(keywords).keys())
    exp_similarity_score = 0
    skill_similarity_score = 0
    e_similarity_score = 0
    s_similarity_score = 0
    course_resume_similarity = 0
    simi = []
    #print(keywords_list)
    for course_keyword in keywords_list:
        if 'skills' in resume_data.keys() and len(resume_data['skills']) != 0:

            for res_keyword in resume_data['skills']:
                course_token = nlp(course_keyword)
                token2 = nlp(res_keyword)
                if (token2.vector_norm):
                    s_similarity_score += course_token.similarity(token2)
                    simi.append((course_token, course_token.similarity(token2)))

            skill_similarity_score = skill_similarity_score + s_similarity_score / len(resume_data['skills'])
        if 'experience' in resume_data.keys() and len(resume_data['experience']) > 2:
            for res_keyword in resume_data['experience']:
                course_token = nlp(course_keyword)
                token2 = nlp(res_keyword)
                if (token2.vector_norm):
                    e_similarity_score += course_token.similarity(token2)
                    simi.append((course_token, course_token.similarity(token2)))

            exp_similarity_score = exp_similarity_score + e_similarity_score / len(resume_data['experience'])
        course_resume_similarity += skill_similarity_score + exp_similarity_score
    course_resume_similarity = course_resume_similarity / len(keywords_list)
    print(
        f"course description '{merged_course_data.split(' :: ')[0].strip()}' similarity with resume experience: {course_resume_similarity}")
    return course_resume_similarity



def get_course_similarity(comments_file: str, resume_file: str,sort_by_similarity_score:bool =True) -> pandas.DataFrame:
    comments_df = pandas.read_csv(comments_file)
    resume_data = parse_resume(resume_file)
    comments_df["merged_data"] = comments_df['Course Name'].astype(str) + " :: " + comments_df['Course Description']
    grouped_df = comments_df.groupby("Course Code")["merged_data"]
    results = []
    for course, group in grouped_df:
        similarity = keyword_parse(resume_data, group)
        results.append(
            {'Course Code': course, 'Subject Name': group.iloc[0].split(' :: ')[0], 'Similarity Score': similarity})

    result_df = pd.DataFrame(results)
    if sort_by_similarity_score:
        result_df = result_df.sort_values(by='Similarity Score', ascending=False)
    return result_df


comments_file = "ucdavis_courses.csv"
resume_file = "ujwal resume.pdf"
df = get_course_similarity(comments_file, resume_file)

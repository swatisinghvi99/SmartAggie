import pandas
import pandas as pd
from pydparser import ResumeParser
from keybert import KeyBERT
import spacy
import sqlite3

sqliteConnection = sqlite3.connect('smartAggie.sqlite')
nlp = spacy.load("en_core_web_lg")
kw_model = KeyBERT(model='all-mpnet-base-v2')


def parse_resume(resume_file: str) -> dict:
    data = ResumeParser(resume_file).get_extracted_data()
    return data


def keyword_parse(resume_data: dict, course_data: pandas.DataFrame, top_n: int = 10) -> float:
    keywords = kw_model.extract_keywords(course_data,
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
    # print(keywords_list)
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
        f"course description '{course_data.split(':')[0].strip()}' similarity with resume experience: {course_resume_similarity}")
    return course_resume_similarity



def get_course_similarity_dept(resume_file: str,department:str='',sort_by_similarity_score:bool =True) -> pandas.DataFrame:
    if department !='':
        comments_df = pandas.read_sql(sql=f"select * from Courses where \"Subject Name\" = \"{department}\";",con=sqliteConnection)
    else:
        comments_df = pandas.read_sql(sql=f"select * from Courses;",con=sqliteConnection)
    resume_data = parse_resume(resume_file)
    grouped_df = comments_df.groupby("Course Code")["Course Description"]
    results = []
    for course, group in grouped_df:
        similarity = keyword_parse(resume_data, group)
        results.append(
            {'Course Code': course, 'Subject Name': group.iloc[0].split(':')[0], 'Similarity Score': similarity})

    result_df = pd.DataFrame(results)
    if sort_by_similarity_score:
        result_df = result_df.sort_values(by='Similarity Score', ascending=False)
    return result_df

def get_course_similarity_course_desc(resume_file: str,course_desc:str=''):
    resume_data = parse_resume(resume_file)
    return keyword_parse(resume_data, course_desc)

if __name__ == "__main__":
    resume_file = "sample resume.pdf"
    # df = get_course_similarity_dept(resume_file, department="Computer Science Engineering ")
    print(get_course_similarity_course_desc(resume_file, 'Computer Science'))

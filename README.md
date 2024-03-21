# SmartAggie: AI Course Selection Assistant
This research explores the integration of data and web technologies in educational data analysis, focusing on predicting student academic performance and providing personalized course recommendations. Leveraging historical data from RateMyProfessors, the UC Davis Course Catalog, and the registrar’s website, we developed a system to predict future academic performance for University of California, Davis (UC Davis) students. Our methodology involves preprocessing and aggregating the data from the above sources, using NLP techniques to compute course and resume similarity as well as comment sentiment analysis. Our prediction algorithm utilizes the metrics obtained earlier and uses unsupervised learning to suggest courses to students along with interactive visualizations of course popularity trends, professor sentiments, and course difficulty, that could aid them in making informed decisions.

## Technologies Used - 
* BeautifulSoup and Selenium (for web scraping)
* SQLlite (for database)
* KeyBERT (for keyword extraction)
* VADER (for sentiment analysis)
* pydparser (for resume parsing)
* Plotly, NetworkX (for visualizations)

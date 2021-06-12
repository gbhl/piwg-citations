This repository contains sample programs used to create and manage articles in **Biodiversity Heritage Library (BHL)**. It will eventually include a series of programs that can be used to perform tasks such as extracting article metadata from BHL and gathering the article metadata needed to define articles in BHL from a variety of sources.  

### Useful references:
* [BHL developer and data tools](https://about.biodiversitylibrary.org/tools-and-services/developer-and-data-tools/)
* [Crossref REST API documentation (from GitHub)](https://github.com/CrossRef/rest-api-doc)
* [crossrefapi documentation (from GitHub)](https://github.com/fabiobatalha/crossrefapi)
* [ISSN portal](https://portal.issn.org/)
* [Python tutorial](https://www.python-course.eu/python3_course.php)



### Programs:
* **cr2bhl.py**
>A python 3 program that gathers article metadata from **Crossref** for the specified **ISSN** and **date range** and writes it to a tsv file. It formats the metadata in a way that allows definition of articles in BHL using the **Import Segments** function. Optionally, this program will match Crossref articles with existing BHL articles.

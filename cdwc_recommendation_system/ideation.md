Persona:
Users : HODs, GMs
Employee: SKG09 Geoscience 

Technical Requirements Gathering:

Q: Do we want to produce insights or just deterministic output? 
Q: If insights, what are the insights that you want to produce?


Q1. Are these 4 excel files the only ones that we will consume for the competency score?

(a) EPDR:
Q2.When profiling the candidates' capabilities, do we want to include the columns "comment(self)", "comment (supervisor)"? 
Challenge: (i) %of missing values are high. (ii) messy
Importance: Contain specific project experience, assessment justifications, competency evidence, supervisor evaluations.
Computing Method:
METHOD 1: Don't compute on them — use them as display context (Simplest, no algorithm change) 
METHOD 2: Extract specific signals from the free text and convert them into structured features that your existing scoring pipeline can consume. 
METHOD 3: LLM-powered text analysis → structured features (Advanced, hybrid approach)
Use an LLM (like the OpenAI integration you already have in your chat parser) to analyze comments and extract structured assessments:

(b) SMA HRIS:
-> What is CBS%? ANS: Competency Bench Strength

(c) Item Catalog Report
Q3. Are we separating leadership competency from technical competency? 

(d) HR Flex Report


